from django.shortcuts import render
from django.db.models import Count
from django.db.models import Prefetch
from blog.models import Comment, Post, Tag


def serialize_post(post, serialized_comments=None, is_teaser=True):
    serialized_post = {
        "title": post.title,
        "author": post.author.username,
        "published_at": post.published_at,
        "slug": post.slug,
        "image_url": post.image.url if post.image else None,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
    }
    if is_teaser:
        serialized_post.update(
            teaser_text=post.text[:200],
            first_tag_title=post.tags.all()[0].title,
            comments_amount=getattr(post, "num_comments", None),
        )
    else:
        serialized_post.update(
            text=post.text,
            comments=serialized_comments if serialized_comments else [],
            likes_amount=post.num_likes,
        )
    return serialized_post


def serialize_tag(tag):
    return {
        "title": tag.title,
        "posts_with_tag": tag.num_posts,
    }


def fetch_most_popular_posts(returned_posts_number):
    return Post.objects.popular()[:returned_posts_number] \
        .prefetch_related("author", Prefetch("tags", queryset=Tag.objects.annotate(num_posts=Count("posts"))))


def fetch_most_fresh_posts(returned_posts_number):
    return Post.objects.all().order_by("-published_at")[:returned_posts_number] \
        .prefetch_related("author", Prefetch("tags", queryset=Tag.objects.annotate(num_posts=Count("posts")))) \
        .annotate(num_comments=Count("comments"))


def fetch_related_posts(tag_title, returned_posts_number):
    return Tag.objects.get(title=tag_title).posts.all() \
        .prefetch_related("author", Prefetch("tags", queryset=Tag.objects.annotate(num_posts=Count("posts")))) \
        .annotate(num_comments=Count("comments"))[0:returned_posts_number]


def index(request):
    most_popular_posts = fetch_most_popular_posts(5)
    most_fresh_posts = fetch_most_fresh_posts(5)
    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        "most_popular_posts": [serialize_post(post) for post in most_popular_posts],
        "page_posts": [serialize_post(post) for post in most_fresh_posts],
        "popular_tags": [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, "index.html", context)


def post_detail(request, slug):
    post = Post.objects.annotate(num_likes=Count("likes")) \
        .prefetch_related("author", Prefetch("tags", queryset=Tag.objects.annotate(num_posts=Count("posts")))) \
        .get(slug=slug)
    comments = Comment.objects.filter(post=post).select_related("author")
    serialized_comments = []
    for comment in comments.all():
        serialized_comments.append({
            "text": comment.text,
            "published_at": comment.published_at,
            "author": comment.author.username,
        })

    serialized_post = serialize_post(post, serialized_comments, is_teaser=False)

    most_popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = fetch_most_popular_posts(5)

    context = {
        "post": serialized_post,
        "popular_tags": [serialize_tag(tag) for tag in most_popular_tags],
        "most_popular_posts": [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, "post-details.html", context)


def tag_filter(request, tag_title):
    related_posts = fetch_related_posts(tag_title, returned_posts_number=20)

    most_popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = fetch_most_popular_posts(returned_posts_number=5)

    context = {
        "tag": tag_title,
        "popular_tags": [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post(post) for post in related_posts],
        "most_popular_posts": [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, "posts-list.html", context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, "contacts.html", {})
