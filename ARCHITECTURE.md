# Backend Architecture

The backend uses a layered structure while retaining the original crawler,
analytics, reporting, and command-line behavior.

```text
api.py
  -> presentation/       HTTP routes and request validation
     -> application/     use-case orchestration and response composition
        -> services/     analytics and domain operations
        -> repositories/ persistence operations
           -> infrastructure/ SQLite connection and schema
```

## Layer responsibilities

- `api.py` creates the FastAPI application and wires its dependencies.
- `presentation` owns HTTP paths, query parameters, and status responses.
- `application` combines repository data and analytics into API use cases.
- `services` contains the existing analytics, sentiment, crawling, and data
  quality logic.
- `repositories` owns article queries and persistence operations.
- `infrastructure` owns SQLite configuration, connections, and schema setup.
- `database/database.py` is a compatibility facade for existing scripts. New
  code should depend on `repositories` or `infrastructure` as appropriate.

Dependencies should point downward through the layers. Infrastructure does not
import application or presentation code.
