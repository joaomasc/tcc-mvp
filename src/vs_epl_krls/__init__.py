"""Independent implementation of VS-ePL-KRLS for online regression."""

from .fuel import (
    FuelEvaluation,
    canonical_product,
    evaluate_fuel_product,
    load_anp_fuel_csv,
    make_lagged_dataset,
)
from .kernels import rbf_features, rbf_kernel, rbf_kernel_matrix
from .krls import KRLSUpdate, SparseKRLS
from .metrics import mae, mse, regression_report, rmse, smape
from .model import VSEPLKRLS, EPLKRLSFixedBeta, VSEPLKRLSConfig
from .news import (
    NEWS_ALL_FEATURES,
    NEWS_CORE_FEATURES,
    NewsFeatureSnapshot,
    augment_supervised_with_news,
    load_weekly_news_features,
)
from .news_annotation import (
    ANNOTATION_COLUMNS,
    AnnotationBatch,
    build_annotation_batch,
    merge_annotation_slots,
    validate_annotations,
)
from .news_annotation_simulation import (
    SimulatedLabel,
    simulate_annotation_slot,
    simulate_label,
)
from .news_pressure import (
    NEWS_PRESSURE_FEATURES,
    NewsCorpusSnapshot,
    NewsPressureConfig,
    NewsPressureFeatures,
    OnlineNewsPressureClassifier,
    WeeklyNewsDocuments,
    augment_supervised_with_pressure,
    build_weekly_news_documents,
    generate_prequential_pressure_features,
    load_news_corpus,
    market_pressure_labels,
)
from .rule import EvolvingRule
from .shadow import (
    S10ResidualHybridShadow,
    S10ShadowForecast,
    S10ShadowHealth,
    append_shadow_ledger,
    verify_shadow_ledger,
)
from .utils import MinMaxScaler, RunningTargetStats

__all__ = [
    "ANNOTATION_COLUMNS",
    "NEWS_ALL_FEATURES",
    "NEWS_CORE_FEATURES",
    "NEWS_PRESSURE_FEATURES",
    "VSEPLKRLS",
    "AnnotationBatch",
    "EPLKRLSFixedBeta",
    "EvolvingRule",
    "FuelEvaluation",
    "KRLSUpdate",
    "MinMaxScaler",
    "NewsCorpusSnapshot",
    "NewsFeatureSnapshot",
    "NewsPressureConfig",
    "NewsPressureFeatures",
    "OnlineNewsPressureClassifier",
    "RunningTargetStats",
    "S10ResidualHybridShadow",
    "S10ShadowForecast",
    "S10ShadowHealth",
    "SimulatedLabel",
    "SparseKRLS",
    "VSEPLKRLSConfig",
    "WeeklyNewsDocuments",
    "append_shadow_ledger",
    "augment_supervised_with_news",
    "augment_supervised_with_pressure",
    "build_annotation_batch",
    "build_weekly_news_documents",
    "canonical_product",
    "evaluate_fuel_product",
    "generate_prequential_pressure_features",
    "load_anp_fuel_csv",
    "load_news_corpus",
    "load_weekly_news_features",
    "mae",
    "make_lagged_dataset",
    "market_pressure_labels",
    "merge_annotation_slots",
    "mse",
    "rbf_features",
    "rbf_kernel",
    "rbf_kernel_matrix",
    "regression_report",
    "rmse",
    "simulate_annotation_slot",
    "simulate_label",
    "smape",
    "validate_annotations",
    "verify_shadow_ledger",
]

__version__ = "0.2.0"
