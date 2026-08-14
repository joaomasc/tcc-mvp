from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd


def expanding_origin_indices(n: int, n_min_train: int, horizon: int) -> List[int]:
    """Origins t such that we predict y[t+horizon] using data up to t."""
    last = n - horizon - 1
    return list(range(n_min_train - 1, last + 1))


def walk_forward_online(
    model_factory: Callable,
    X: np.ndarray,
    y: np.ndarray,
    n_min_train: int,
    horizon: int = 1,
) -> Dict[str, np.ndarray]:
    """Predict y[t+h] from X[t] after training on pairs up to origin t.

    For an online model the factory is called once; we stream update(X[k], y[k])
    using the contemporaneous pair (features at k, target at k which is already
    lagged/shifted so that y[k] is the h-step target known only after h weeks).

    Leak-safe protocol:
      at origin t we may use X[0..t] and y[0..t-1] (y[t] is the h-step target
      that realizes at t+h, so it is NOT known at t). We predict yhat[t] from
      X[t], then when the next origin arrives we update with the newly realized
      target.
    """
    model = model_factory()
    n = len(y)
    yhat = np.full(n, np.nan)
    n_rules = np.full(n, np.nan)
    betas = np.full(n, np.nan)
    for t in range(n):
        if t == 0:
            yhat[t] = model.predict_one(X[t]) if model.n_rules else np.nan
            continue
        # y[t-1] has just become available in a delayed sense only when t-1+h
        # has passed. In the supervised matrix, row t already uses lagged
        # features, and y[t] is revenda[t+h]. To avoid using future y we update
        # with the previous realized pair after predicting.
        yhat[t] = model.predict_one(X[t]) if model.n_rules else np.nan
        if t >= 1:
            model.update(X[t - 1], float(y[t - 1]))
        n_rules[t] = getattr(model, "n_rules", np.nan)
        betas[t] = getattr(model, "beta", np.nan)
    if n >= 1:
        model.update(X[n - 1], float(y[n - 1]))
    mask = ~np.isnan(yhat)
    mask[: max(n_min_train, 1)] = False
    return {
        "yhat": yhat,
        "mask": mask,
        "n_rules": n_rules,
        "beta": betas,
        "model": model,
    }


def walk_forward_batch(
    fit_predict: Callable,
    X: np.ndarray,
    y: np.ndarray,
    n_min_train: int,
    refit_every: int = 4,
    extra: Optional[dict] = None,
) -> Dict[str, np.ndarray]:
    n = len(y)
    yhat = np.full(n, np.nan)
    last_model = None
    last_fit_end = -10**9
    extra = extra or {}
    for t in range(n_min_train, n):
        if t - last_fit_end >= refit_every or last_model is None:
            last_model = fit_predict(X[:t], y[:t], X[t : t + 1], **extra)
            last_fit_end = t
            yhat[t] = last_model[0]
        else:
            yhat[t] = fit_predict(X[:t], y[:t], X[t : t + 1], model=last_model[1], **extra)[0]
    mask = ~np.isnan(yhat)
    return {"yhat": yhat, "mask": mask}
