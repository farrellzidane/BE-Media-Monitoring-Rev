# Backend Architecture

The backend uses a layered structure while retaining the original crawler,
analytics, reporting, and command-line behavior.

```text
api.py
  -> presentation/       HTTP routes and request validation
     -> application/     use-case orchestration and response composition
        -> services/     analytics and domain operations
        -> repositories/ persistence operations
           -> infrastructure/ PostgreSQL pool and schema
```

## Layer responsibilities

- `api.py` creates the FastAPI application and wires its dependencies.
- `presentation` owns HTTP paths, query parameters, and status responses.
- `application` combines repository data and analytics into API use cases.
- `services` contains the existing analytics, sentiment, crawling, and data
  quality logic.
- `repositories` owns article queries and persistence operations.
- `infrastructure` owns PostgreSQL configuration, pooled connections, and
  schema setup.
- `database/database.py` is a compatibility facade for existing scripts. New
  code should depend on `repositories` or `infrastructure` as appropriate.

Dependencies should point downward through the layers. Infrastructure does not
import application or presentation code.

## Data-quality scoring

`services/data_quality_service.py` evaluates every article with normalized,
weighted rules grouped into five dimensions:

- completeness: 35%
- validity: 20%
- uniqueness: 20%
- timeliness: 15%
- consistency: 10%

Each rule score is `passed / applicable * 100`; the overall score is the sum of
the rule scores multiplied by their configured weights. Rule weights,
thresholds, supported categories, and crawl timing limits live in
`config/settings.py`. The `/analytics` response exposes the overall result,
dimension breakdown, rule-level pass/fail counts, and source health. Legacy
summary fields remain available for the older Streamlit consumer.

Rule-level evidence is loaded separately from
`GET /data-quality/rules/{rule_key}/evidence`. The endpoint supports
`result=all|passed|failed`, `limit`, and `offset`, and returns the observed
value, expected condition, decision reason, and article/source identity. This
keeps the main analytics payload small while allowing the React dashboard to
drill into every score.
