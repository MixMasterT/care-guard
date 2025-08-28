# Medical Knowledge Base Index Documentation

## Index Name

`medical-knowledge-base`

## Index Structure (Mapping)

| Field              | Type    | Description                                             | Notes                                        |
| ------------------ | ------- | ------------------------------------------------------- | -------------------------------------------- |
| `title`            | text    | Article title, full-text searchable                     | Includes keyword subfield for exact matching |
| `source`           | keyword | Publication source or journal name                      | Exact match for filtering/search             |
| `publication_date` | date    | Publication date in `yyyy-MM-dd` format                 | Useful for date range filtering/sorting      |
| `url`              | keyword | URL link to the article                                 | Stored but not searchable                    |
| `medical_terms`    | keyword | Array of important medical terms extracted from article | Useful for faceted search/filter             |
| `topic_category`   | keyword | The assigned topic category of the article              | For topical filtering                        |
| `indexed_at`       | date    | Timestamp when document was indexed                     | System field for tracking                    |
| `relevance_score`  | float   | Relevance score (0.0-1.0)                               | For ranking and filtering                    |

## Querying the Index

### Full-text search example

```json
{
  "query": {
    "match": {
      "title": "remote patient monitoring"
    }
  }
}
```

### Filtering by topic

```json
{
  "query": {
    "bool": {
      "must": {
        "match": {
          "content": "telehealth"
        }
      },
      "filter": {
        "term": {
          "topic_category": "Live Monitoring of Patient Vitals Post-Cardiac Surgery"
        }
      }
    }
  }
}
```

### Search by medical terms with exact match

```json
{
  "query": {
    "terms": {
      "medical_terms": ["cardiac surgery", "complications"]
    }
  }
}
```

### Date range query example

```json
{
  "query": {
    "range": {
      "publication_date": {
        "gte": "2020-01-01",
        "lte": "2022-12-31"
      }
    }
  }
}
```

### Multi-field search with relevance filtering

```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "title": "cardiac monitoring" } },
        { "match": { "medical_terms": "cardiac monitoring" } }
      ],
      "minimum_should_match": 1,
      "filter": {
        "range": {
          "relevance_score": { "gte": 0.8 }
        }
      }
    }
  }
}
```

---

## Pydantic Model

```python
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, HttpUrl, Field

class MedicalArticle(BaseModel):
    title: str = Field(..., description="Title of the medical article")
    source: str = Field(..., description="Publication source or journal name")
    publication_date: Optional[date] = Field(None, description="Publication date in ISO format")
    url: Optional[HttpUrl] = Field(None, description="URL link to the article")
    medical_terms: List[str] = Field(default_factory=list, description="List of relevant medical terms")
    topic_category: str = Field(..., description="Topic category assigned to the article")
    indexed_at: Optional[datetime] = Field(default_factory=datetime.now, description="Indexing timestamp")
    relevance_score: float = Field(1.0, ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")

# Example usage:
# article = MedicalArticle(
#     title="Sample title",
#     source="Journal Name",
#     publication_date=date(2021, 1, 1),
#     url="https://example.com/article",
#     medical_terms=["cardiac surgery", "monitoring"],
#     topic_category="Live Monitoring of Patient Vitals Post-Cardiac Surgery"
# )
```

---

## Verification of Search

Sample query to check articles containing 'cardiac surgery':

```json
{
  "query": {
    "match": {
      "title": "cardiac surgery"
    }
  }
}
```

This will return ranked articles related to cardiac surgery with titles, sources, and dates for easy retrieval and indexing.

---

## Performance Guidelines

- **Use filters for exact matches** (faster than queries)
- **Limit result size** with `"size": 10` for large datasets
- **Combine match + filter** for optimal performance
- **Use aggregations** for analytics: `"aggs": {"sources": {"terms": {"field": "source"}}}`
