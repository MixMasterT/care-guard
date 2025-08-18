from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TopicCategory(str, Enum):
    """Enumeration of medical knowledge topic categories."""
    PATIENT_MONITORING = "patient_monitoring"
    POST_OP_RECOVERY = "post_op_recovery"
    VITAL_SIGNS = "vital_signs"
    COMPLICATIONS = "complications"
    INTERVENTION_PROTOCOLS = "intervention_protocols"

class ArticleType(str, Enum):
    """Enumeration of medical article types."""
    CLINICAL_GUIDELINE = "clinical_guideline"
    RESEARCH_PAPER = "research_paper"
    CASE_STUDY = "case_study"
    REVIEW_ARTICLE = "review_article"
    META_ANALYSIS = "meta_analysis"
    CLINICAL_TRIAL = "clinical_trial"
    EXPERT_OPINION = "expert_opinion"

class MedicalKnowledgeDocument(BaseModel):
    """Pydantic model for medical knowledge documents to be indexed in OpenSearch."""
    
    # Core document fields
    title: str = Field(..., description="Title of the medical article or document")
    content: str = Field(..., description="Full content of the medical article")
    source: str = Field(..., description="Source of the article (e.g., PubMed, Clinical Guidelines, Journal Name)")
    url: Optional[HttpUrl] = Field(None, description="URL to the original article")
    
    # Metadata fields
    publication_date: Optional[datetime] = Field(None, description="Publication date of the article")
    author: Optional[str] = Field(None, description="Author(s) of the article")
    institution: Optional[str] = Field(None, description="Institution or organization associated with the article")
    article_type: ArticleType = Field(ArticleType.RESEARCH_PAPER, description="Type of medical article")
    
    # Categorization fields
    topic_category: TopicCategory = Field(..., description="Primary topic category of the article")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the article")
    medical_terms: List[str] = Field(default_factory=list, description="Specific medical terms mentioned in the article")
    
    # Quality and relevance fields
    relevance_score: float = Field(1.0, ge=0.0, le=1.0, description="Relevance score for the medical knowledge base (0.0 to 1.0)")
    
    # System fields
    indexed_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the document was indexed")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicalKnowledgeSearchQuery(BaseModel):
    """Pydantic model for medical knowledge search queries."""
    
    query_text: str = Field(..., description="Text to search for in the medical knowledge base")
    topic_categories: Optional[List[TopicCategory]] = Field(None, description="Filter by topic categories")
    article_types: Optional[List[ArticleType]] = Field(None, description="Filter by article types")
    sources: Optional[List[str]] = Field(None, description="Filter by specific sources")
    medical_terms: Optional[List[str]] = Field(None, description="Filter by specific medical terms")
    min_relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum relevance score")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True

class MedicalKnowledgeIndexConfig(BaseModel):
    """Pydantic model for medical knowledge index configuration."""
    
    index_name: str = Field("medical-knowledge-base", description="Name of the OpenSearch index")
    number_of_shards: int = Field(1, ge=1, description="Number of shards for the index")
    number_of_replicas: int = Field(0, ge=0, description="Number of replicas for the index")
    max_result_window: int = Field(10000, ge=1000, description="Maximum result window for searches")
    
    # Mapping configuration
    enable_text_analysis: bool = Field(True, description="Enable text analysis for content fields")
    enable_keyword_search: bool = Field(True, description="Enable keyword search capabilities")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "index_name": "medical-knowledge-base",
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "max_result_window": 10000,
                "enable_text_analysis": True,
                "enable_keyword_search": True
            }
        }

class MedicalKnowledgeIndexStats(BaseModel):
    """Pydantic model for medical knowledge index statistics."""
    
    index_name: str = Field(..., description="Name of the index")
    document_count: int = Field(..., ge=0, description="Total number of documents in the index")
    topic_category_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of documents by topic category")
    article_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of documents by article type")
    source_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of documents by source")
    average_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Average relevance score of all documents")
    last_indexed: Optional[datetime] = Field(None, description="Timestamp of the last document indexed")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicalKnowledgeSearchResult(BaseModel):
    """Pydantic model for medical knowledge search results."""
    
    document_id: str = Field(..., description="OpenSearch document ID")
    score: float = Field(..., description="Search relevance score")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source")
    topic_category: TopicCategory = Field(..., description="Document topic category")
    article_type: ArticleType = Field(..., description="Document article type")
    relevance_score: float = Field(..., description="Document relevance score")
    publication_date: Optional[datetime] = Field(None, description="Document publication date")
    content_preview: Optional[str] = Field(None, description="Preview of document content")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Utility functions for working with medical knowledge documents

def create_medical_document(
    title: str,
    content: str,
    source: str,
    topic_category: TopicCategory,
    url: Optional[str] = None,
    publication_date: Optional[datetime] = None,
    author: Optional[str] = None,
    institution: Optional[str] = None,
    article_type: ArticleType = ArticleType.RESEARCH_PAPER,
    keywords: Optional[List[str]] = None,
    medical_terms: Optional[List[str]] = None,
    relevance_score: float = 1.0
) -> MedicalKnowledgeDocument:
    """
    Create a medical knowledge document with proper validation.
    
    Args:
        title: Document title
        content: Document content
        source: Document source
        topic_category: Primary topic category
        url: Optional URL to original article
        publication_date: Optional publication date
        author: Optional author information
        institution: Optional institution information
        article_type: Type of medical article
        keywords: Optional list of keywords
        medical_terms: Optional list of medical terms
        relevance_score: Relevance score (0.0 to 1.0)
    
    Returns:
        Validated MedicalKnowledgeDocument
    """
    return MedicalKnowledgeDocument(
        title=title,
        content=content,
        source=source,
        topic_category=topic_category,
        url=url,
        publication_date=publication_date,
        author=author,
        institution=institution,
        article_type=article_type,
        keywords=keywords or [],
        medical_terms=medical_terms or [],
        relevance_score=relevance_score
    )

def validate_medical_document(document_dict: Dict[str, Any]) -> MedicalKnowledgeDocument:
    """
    Validate a dictionary and convert it to a MedicalKnowledgeDocument.
    
    Args:
        document_dict: Dictionary containing document data
    
    Returns:
        Validated MedicalKnowledgeDocument
    
    Raises:
        ValidationError: If the document data is invalid
    """
    return MedicalKnowledgeDocument(**document_dict) 