"""Utility functions to work with bound constraints."""


import numpy as np


def prepare_bounds(bounds, x0):
    """Prepare bounds for usage in algorithms."""
    lb, ub = [np.asarray(b, dtype=float) for b in bounds]
    if lb.ndim == 0:
        lb = np.resize(lb, x0.shape)

    if ub.ndim == 0:
        ub = np.resize(ub, x0.shape)

    return lb, ub


def in_bounds(x, lb, ub):
    """Check if the point lies within the bounds."""
    return np.all((x >= lb) & (x <= ub))


def step_size_to_bound(x, d, lb, ub):
    """Compute a step size required to reach the bounds.

    The function computes a positive scalar t, such that x + t * d is on
    the bound.

    Returns
    -------
    step : float
        Computed step.
    hit : array of int with shape of x
        Each component shows whether a corresponding variable reaches the
        bound:
             0 - the bound was not hit.
            -1 - the lower bound was hit.
             1 - the upper bound was hit.
    """
    non_zero = np.nonzero(d)
    d_nz = d[non_zero]
    steps = np.full_like(x, np.inf)
    with np.errstate(over='ignore'):
        steps[non_zero] = np.maximum((lb - x)[non_zero] / d_nz,
                                     (ub - x)[non_zero] / d_nz)
    step = np.min(steps)
    return step, np.equal(steps, step) * np.sign(d).astype(int)


def find_active_constraints(x, lb, ub, rtol=1e-12):
    """Determine which constraints are active in the given point.

    The threshold is computed using `rtol` and the absolute value of the
    closest bound.

    Returns
    ------
    active : ndarray of int with shape of x
        Each component shows whether the corresponding constraint is active:
             0 - a constraint is not active.
            -1 - a lower bound is active.
             1 - a upper bound is active.
    """
    active = np.zeros_like(x, dtype=int)

    lower_dist = x - lb
    upper_dist = ub - x

    mask = lower_dist < upper_dist
    value = lower_dist[mask] < rtol * np.maximum(1, np.abs(lb[mask]))
    active[mask] = -value.astype(int)
    value = upper_dist[~mask] < rtol * np.maximum(1, np.abs(ub[~mask]))
    active[~mask] = value.astype(int)

    return active


def make_strictly_feasible(x, lb, ub, rstep=0):
    """Shift the point in the slightest possible way to the interior.

    If ``rstep=0`` the function uses np.nextafter, otherwise `rstep` is
    multiplied by absolute value of the bound.

    The utility of this function is questionable to me. Maybe bigger shifts
    should be used, or maybe this function is not necessary at all despite
    theoretical requirement of our interior point algorithm.
    """
    x_new = x.copy()

    m = x <= lb
    if rstep == 0:
        x_new[m] = np.nextafter(lb[m], ub[m])
    else:
        x_new[m] = lb[m] + rstep * (1 + np.abs(lb[m]))

    m = x >= ub
    if rstep == 0:
        x_new[m] = np.nextafter(ub[m], lb[m])
    else:
        x_new[m] = ub[m] - rstep * (1 + np.abs(ub[m]))

    return x_new


def CL_scaling(x, g, lb, ub):
    """Compute a scaling vector and its derivatives as described in papers
    of Coleman and Li."""
    d = np.ones_like(x)
    jv = np.zeros_like(x)
    mask = (g < 0) & np.isfinite(ub)
    d[mask] = ub[mask] - x[mask]
    jv[mask] = -1
    mask = (g > 0) & np.isfinite(lb)
    d[mask] = x[mask] - lb[mask]
    jv[mask] = 1

    return d**0.5, jv


def CL_optimality(x, g, lb, ub):
    lb = np.resize(lb, x.shape)
    ub = np.resize(ub, x.shape)
    d, _ = CL_scaling(x, g, lb, ub)
    return np.linalg.norm(d**2 * g, ord=np.inf)
