from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    field_validator,
)


class GetImageRequest(BaseModel):
    """Validation model for get image request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    image_id: StrictStr = Field(
        ...,
        min_length=1,
        description="Image ID to retrieve",
    )

    metadata: StrictBool = Field(
        default=False,
        description="Include metadata in response headers",
    )

    download: StrictBool = Field(
        default=False,
        description=(
            "If true, forces image download "
            "(Content-Disposition: attachment). "
            "If false, displays image inline."
        ),
    )

    @field_validator("image_id")
    @classmethod
    def validate_image_id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("image_id must not be blank")
        return value


class ImageMetadataHeader(BaseModel):
    """Metadata to include in response header."""

    image_id: str
    user_id: str
    image_name: str
    description: str | None = None
    tags: list[str] | None = None
    created_at: str
    file_size: int
    mime_type: str
