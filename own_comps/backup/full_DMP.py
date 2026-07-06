"""
Script CHOP Callbacks

me - this DAT

scriptOp - the OP which is cooking
"""

import numpy as np

class SimpleDMP:
    def __init__(self, n_dofs=6, n_basis=50, alpha_z=25.0, beta_z=None, alpha_x=25.0/3.0):
        self.n_dofs = n_dofs
        self.n_basis = n_basis
        self.alpha_z = alpha_z
        self.beta_z = beta_z if beta_z is not None else alpha_z / 4.0
        self.alpha_x = alpha_x if alpha_x is not None else alpha_z / 3.0

        self.c = np.exp(-self.alpha_x * np.linspace(0.0, 1.0, self.n_basis))
        self.h = (self.n_basis ** 1.5) / (self.c + 1e-12)
        self.w = np.zeros((self.n_dofs, self.n_basis))
        
        # Store the learned amplitude for each DOF
        self.A = np.ones(self.n_dofs) 
        
    def imitate(self, pos, vel=None, dt=0.01):
        """Train on joint position trajectory (velocities optional)"""
        pos = np.asarray(pos, dtype=np.float64)
        T = len(pos)
        if T < 2:
            raise ValueError('Need at least 2 samples to train DMP.')

        if vel is None:
            vel = np.gradient(pos, dt, axis=0)
        else:
            vel = np.asarray(vel, dtype=np.float64)

        acc = np.gradient(vel, dt, axis=0)
        tau = (T - 1) * dt

        t = np.arange(T) * dt
        x = np.exp(-self.alpha_x * t / tau)
        psi = np.exp(-self.h[None, :] * (x[:, None] - self.c[None, :]) ** 2)
        psi_sum = np.sum(psi, axis=1, keepdims=True) + 1e-12

        g = pos[-1]
        
        # Calculate amplitude A = max(y) - min(y) for each DOF
        self.A = np.max(pos, axis=0) - np.min(pos, axis=0)
        
        # Fallback to prevent division by zero on completely flat trajectories
        self.A[self.A < 1e-8] = 1.0 

        for dof in range(self.n_dofs):
            f_target = (
                (tau ** 2) * acc[:, dof]
                - self.alpha_z * (self.beta_z * (g[dof] - pos[:, dof]) - tau * vel[:, dof])
            )

            # Scale using amplitude A instead of (g - y0)
            scale = self.A[dof]

            design = (psi / psi_sum) * x[:, None]
            self.w[dof] = np.linalg.lstsq(design, f_target / scale, rcond=None)[0]
    
    def roll_out(self, y0, g, A=None, tau=1.0, dt=0.01, T=1000):
        """Generate trajectory from initial/goal states"""
        y0 = np.asarray(y0, dtype=np.float64)
        g = np.asarray(g, dtype=np.float64)
        
        # If no new amplitude is provided, default to the learned amplitude
        if A is None:
            A = self.A
        else:
            A = np.asarray(A, dtype=np.float64)
            
        y = np.zeros((T, self.n_dofs), dtype=np.float64)
        z = np.zeros((T, self.n_dofs), dtype=np.float64)
        y[0] = y0

        x = 1.0
        for i in range(1, T):
            x_dot = -self.alpha_x * x / tau
            x += x_dot * dt
            x = max(x, 1e-8)

            psi = np.exp(-self.h * (x - self.c) ** 2)
            psi_sum = np.sum(psi) + 1e-12

            f = np.zeros(self.n_dofs, dtype=np.float64)
            for dof in range(self.n_dofs):
                # Scale using the decoupled amplitude A
                scale = A[dof]
                f[dof] = (np.dot(self.w[dof], psi) / psi_sum) * x * scale

            z_dot = (self.alpha_z * (self.beta_z * (g - y[i - 1]) - z[i - 1]) + f) / tau
            y_dot = z[i - 1] / tau

            z[i] = z[i - 1] + z_dot * dt
            y[i] = y[i - 1] + y_dot * dt

        return y
    



from typing import Any


def _read_trajectories_from_input_chop(input_chop):
    """
    Read one or more (name, trajectory[T, 6]) entries from an input CHOP.
    - 6 channels -> one trajectory
    - 6*N channels -> N trajectories from contiguous groups of 6 channels
    """
    channels = input_chop.chans()
    channel_count = len(channels)

    if channel_count < 6:
        raise ValueError(f'needs at least 6 channels, got {channel_count}')
    if channel_count % 6 != 0:
        raise ValueError(f'channel count must be a multiple of 6, got {channel_count}')

    values = np.stack([np.asarray(channel.vals, dtype=np.float64) for channel in channels], axis=1)
    num_movements = channel_count // 6

    trajectories = []
    for movement_index in range(num_movements):
        start = movement_index * 6
        stop = start + 6
        trajectory = values[:, start:stop]
        name = input_chop.name if num_movements == 1 else f'{input_chop.name}_{movement_index}'
        trajectories.append((name, trajectory))

    return trajectories

# press 'Setup Parameters' in the OP to call this function to re-create the
# parameters.

def _extract_full_feature_vector(dmp, goal_pos, amplitude):
    """
    Extract full feature vector from trained DMP with goal and amplitude.
    Returns: 1D array with [w_flattened (300), g (6), A (6)], total length 312
    """
    w_flat = dmp.w.flatten()  # (6, 50) -> (300,)
    goal_flat = np.asarray(goal_pos, dtype=np.float64).flatten()  # (6,)
    amplitude_flat = np.asarray(amplitude, dtype=np.float64).flatten()  # (6,)
    
    feature_vec = np.concatenate([w_flat, goal_flat, amplitude_flat])
    return feature_vec  # Shape: (312,)


def onPulse(par: Any):
    """
    Called when a custom pulse parameter is pushed.
    Loads trajectories from Script CHOP inputs and extracts DMP feature vectors.

    Args:
        par: The parameter that was pulsed
    """
    
    if par.name == 'Createdmp':

        scriptOp = par.owner

        input_chops = [chop for chop in scriptOp.inputs if chop is not None]
        if not input_chops:
            print('Error: No input CHOPs connected.')
            return

        print(f'Loading trajectories from {len(input_chops)} input CHOP(s).')
        
        feature_vectors = []
        trajectory_names = []
        generated_trajectories = []
        
        for idx, input_chop in enumerate(input_chops):
            try:
                trajectories = _read_trajectories_from_input_chop(input_chop)
            except Exception as e:
                print(f'  [{idx+1}] Error in input "{input_chop.name}": {e}. Skipping.')
                continue

            for movement_name, joint_traj in trajectories:
                if joint_traj.shape[0] < 2:
                    print(f'  [{idx+1}] Skipping "{movement_name}": need at least 2 samples.')
                    continue

                dmp = SimpleDMP(n_dofs=6, n_basis=50)
                dt = 1.0 / max(me.time.rate, 1)

                try:
                    dmp.imitate(joint_traj, dt=dt)
                except Exception as e:
                    print(f'  [{idx+1}] Error training DMP for "{movement_name}": {e}. Skipping.')
                    continue

                # goal_pos = joint_traj[-1]
                # feature_vec = _extract_full_feature_vector(dmp, goal_pos, dmp.A)

                # feature_vectors.append(feature_vec)
                # trajectory_names.append(movement_name)
                # print(f'  [{idx+1}] Feature vector extracted for "{movement_name}" (length {len(feature_vec)})')

                # roll out trajectory and store
                y0 = joint_traj[0]
                g = joint_traj[-1]
                tau = max((joint_traj.shape[0] - 1) * dt, dt)
                generated = dmp.roll_out(y0=y0, g=g, tau=tau, dt=dt, T=joint_traj.shape[0])
                print(f'  [{idx+1}] Rolled out trajectory for "{movement_name}" with shape {generated.shape}')
                generated_trajectories.append(generated)
                trajectory_names.append(movement_name)

        
        # scriptOp.store('feature_vectors', feature_vectors)
        # scriptOp.store('trajectory_names', trajectory_names)
        scriptOp.store('new_trajectories', generated_trajectories)
        scriptOp.store('new_trajectory_names', trajectory_names)
        scriptOp.par.cookpulse.pulse()
    
    return

def onCook(scriptOp: scriptCHOP):
    """
    Called when the Script CHOP needs to cook.
    """
    scriptOp.clear()

    trajectories = scriptOp.fetch('new_trajectories', None)
    if trajectories is None or len(trajectories) == 0:
        print('Error: No trajectories were generated.')
        return

    trajectory_names = scriptOp.fetch('new_trajectory_names', None)
    if trajectory_names is None:
        trajectory_names = [f'query_{i}' for i in range(len(trajectories))]

    first = np.asarray(trajectories[0], dtype=np.float64)
    if first.ndim != 2:
        print(f'Error: Expected trajectory shape [T, n_dofs], got {first.shape}.')
        return

    n_samples, n_dofs = first.shape
    scriptOp.numSamples = int(n_samples)

    for traj_idx, traj in enumerate(trajectories):
        arr = np.asarray(traj, dtype=np.float64)
        if arr.shape != (n_samples, n_dofs):
            continue
        base = trajectory_names[traj_idx]
        for dof in range(n_dofs):
            chan = scriptOp.appendChan(f'{base}_dof{dof}')
            chan.vals = arr[:, dof].tolist()
    return

def onGetCookLevel(scriptOp: scriptCHOP) -> CookLevel:
	"""
	Sets the scriptOp's cook level, the conditions necessary to cause a cook.

	Return one of the following:
		CookLevel.AUTOMATIC - inputs changed and output being used. TD default
		                      behavior.
		CookLevel.ON_CHANGE - inputs changed, output used or not.
		CookLevel.WHEN_USED - every frame when output is being used
		CookLevel.ALWAYS - every frame
	"""

	return CookLevel.AUTOMATIC

def onSetupParameters(scriptOp):
	"""Auto-generated by Component Editor"""
	# manual changes to anything other than parJSON will be	# destroyed by Comp Editor unless doc string above is	# changed

	TDJSON = op.TDModules.mod.TDJSON
	parJSON = """
	{
		"Custom": {
			"Createdmp": {
				"name": "Createdmp",
				"tupletName": "Createdmp",
				"label": "Create DMP",
				"page": "Custom",
				"sequence": null,
				"style": "Pulse",
				"size": 1,
				"defaultMode": "CONSTANT",
				"default": false,
				"defaultExpr": "",
				"defaultBindExpr": "",
				"enable": true,
				"startSection": false,
				"readOnly": false,
				"enableExpr": null,
				"help": ""
			}
		}
	}
	"""
	parData = TDJSON.textToJSON(parJSON)
	TDJSON.addParametersFromJSONOp(scriptOp, parData, destroyOthers=True)