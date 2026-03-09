"""
Serializers for books app.
"""

from rest_framework import serializers

from .models import Author, Book, BookImage, Genre, Publisher


class GenreSerializer(serializers.ModelSerializer):
    book_count = serializers.ReadOnlyField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "parent",
            "book_count",
            "children",
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return GenreSerializer(children, many=True).data


class AuthorListSerializer(serializers.ModelSerializer):
    book_count = serializers.ReadOnlyField()

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "slug",
            "photo",
            "nationality",
            "book_count",
        ]


class AuthorDetailSerializer(serializers.ModelSerializer):
    book_count = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    books = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "slug",
            "bio",
            "photo",
            "birth_date",
            "death_date",
            "nationality",
            "website",
            "twitter_handle",
            "book_count",
            "average_rating",
            "books",
        ]

    def get_books(self, obj):
        books = obj.books.filter(is_active=True).order_by("-publication_date")[:20]
        return BookListSerializer(books, many=True, context=self.context).data


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "website",
            "founded_year",
            "headquarters",
        ]


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ["id", "image", "image_type", "alt_text", "display_order"]


class BookListSerializer(serializers.ModelSerializer):
    """Compact book serializer for list views."""

    authors = AuthorListSerializer(many=True, read_only=True)
    genres = serializers.StringRelatedField(many=True, read_only=True)
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()
    primary_author = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "slug",
            "isbn_13",
            "short_description",
            "cover_image",
            "thumbnail",
            "authors",
            "genres",
            "primary_author",
            "price",
            "sale_price",
            "effective_price",
            "discount_percentage",
            "average_rating",
            "rating_count",
            "review_count",
            "in_stock",
            "format",
            "publication_date",
        ]

    def get_primary_author(self, obj):
        author = obj.authors.first()
        if author:
            return {"id": str(author.id), "name": author.name}
        return None


class BookDetailSerializer(serializers.ModelSerializer):
    """Full book serializer for detail views."""

    authors = AuthorDetailSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    images = BookImageSerializer(many=True, read_only=True)
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()
    related_books = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "slug",
            "isbn_10",
            "isbn_13",
            "description",
            "short_description",
            "cover_image",
            "thumbnail",
            "images",
            "authors",
            "genres",
            "publisher",
            "publication_date",
            "page_count",
            "language",
            "format",
            "edition",
            "series_name",
            "series_number",
            "price",
            "sale_price",
            "effective_price",
            "discount_percentage",
            "stock_quantity",
            "in_stock",
            "average_rating",
            "rating_count",
            "review_count",
            "tags",
            "weight_grams",
            "dimensions",
            "is_featured",
            "related_books",
            "created_at",
            "updated_at",
        ]

    def get_related_books(self, obj):
        """Get books in the same genres."""
        genre_ids = obj.genres.values_list("id", flat=True)
        related = (
            Book.objects.filter(genres__in=genre_ids, is_active=True)
            .exclude(id=obj.id)
            .distinct()
            .order_by("-average_rating")[:8]
        )
        return BookListSerializer(related, many=True, context=self.context).data


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating books (admin)."""

    author_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True
    )
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )
    publisher_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Book
        fields = [
            "title",
            "isbn_10",
            "isbn_13",
            "description",
            "short_description",
            "cover_image",
            "author_ids",
            "genre_ids",
            "publisher_id",
            "publication_date",
            "page_count",
            "language",
            "format",
            "edition",
            "series_name",
            "series_number",
            "price",
            "sale_price",
            "stock_quantity",
            "is_available",
            "is_featured",
            "tags",
            "weight_grams",
            "dimensions",
        ]

    def create(self, validated_data):
        author_ids = validated_data.pop("author_ids")
        genre_ids = validated_data.pop("genre_ids")
        publisher_id = validated_data.pop("publisher_id", None)

        if publisher_id:
            validated_data["publisher"] = Publisher.objects.get(id=publisher_id)

        book = Book.objects.create(**validated_data)
        book.authors.set(Author.objects.filter(id__in=author_ids))
        book.genres.set(Genre.objects.filter(id__in=genre_ids))
        return book

    def update(self, instance, validated_data):
        author_ids = validated_data.pop("author_ids", None)
        genre_ids = validated_data.pop("genre_ids", None)
        publisher_id = validated_data.pop("publisher_id", None)

        if publisher_id:
            instance.publisher = Publisher.objects.get(id=publisher_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if author_ids is not None:
            instance.authors.set(Author.objects.filter(id__in=author_ids))
        if genre_ids is not None:
            instance.genres.set(Genre.objects.filter(id__in=genre_ids))

        return instance
