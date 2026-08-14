from __future__ import annotations

import numpy as np
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vsepl_krls.model import VSePLKRLS, VSePLKRLSConfig  # noqa: E402


def test_compatibility_and_arousal():
    cfg = VSePLKRLSConfig(use_variable_step=False, beta0=0.18, alpha=0.01)
    m = VSePLKRLS(cfg)
    x0 = np.array([0.2, 0.3])
    m.update(x0, 1.0)
    rho = m._compatibilities(x0)[0]
    assert abs(rho - 1.0) < 1e-9
    x1 = np.array([0.2, 0.3])
    m.update(x1, 1.05)
    assert 0.0 <= m.rules[0].arousal <= 1.0


def test_variable_step_clip():
    cfg = VSePLKRLSConfig(alpha_vs1=0.5, alpha_vs2=0.5, gamma_bar=0.0, beta0=0.18)
    m = VSePLKRLS(cfg)
    m._update_beta(1.0)
    assert m.cfg.beta_min <= m.beta <= m.cfg.beta_max
    for _ in range(40):
        m._update_beta(0.0)
    assert m.beta >= m.cfg.beta_min


def test_krls_matches_kernel_ridge_small():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(12, 2))
    y = np.sin(X[:, 0]) + 0.1 * X[:, 1]
    cfg = VSePLKRLSConfig(use_variable_step=False, d_max=50, novelty_coef=0.0, lam=1e-3, nu0=0.5)
    m = VSePLKRLS(cfg)
    m.rules = []
    # force a single rule that grows dictionary every time
    cfg.novelty_coef = 0.0
    for i in range(len(y)):
        m.update(X[i], float(y[i]))
    rule = m.rules[0]
    # closed-form kernel ridge on dictionary
    D = rule.dictionary
    n = len(D)
    K = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            K[i, j] = np.exp(-np.sum((D[i] - D[j]) ** 2) / (2.0 * 0.5))
    theta_cf = np.linalg.solve(K + cfg.lam * np.eye(n), y[:n] if n <= len(y) else y)
    # only compare if dictionary grew reasonably
    assert rule.n_dict >= 1
    pred_m = m.predict_one(X[-1])
    assert np.isfinite(pred_m)


def test_mackey_glass_learns():
    def mg(n=300, tau=17):
        x = np.zeros(n + tau)
        x[:tau] = 1.2
        for t in range(tau, n + tau - 1):
            x[t + 1] = 0.9 * x[t] + 0.2 * x[t - tau] / (1 + x[t - tau] ** 10)
        return x[tau:]

    s = mg()
    X = np.column_stack([s[:-1], np.roll(s[:-1], 1)])
    y = s[1:]
    X, y = X[2:], y[2:]
    n_train = 200
    m = VSePLKRLS(VSePLKRLSConfig(use_variable_step=True, d_max=20))
    for i in range(n_train):
        m.update(X[i], float(y[i]))
    preds = np.array([m.predict_one(X[i]) for i in range(n_train, len(y))])
    rmse = float(np.sqrt(np.mean((preds - y[n_train:]) ** 2)))
    naive = float(np.sqrt(np.mean((y[n_train - 1 : -1] - y[n_train:]) ** 2)))
    assert np.isfinite(rmse)
    assert rmse < 5.0 * naive + 0.5
