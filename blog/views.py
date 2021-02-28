from django.shortcuts import render
from django.db.models import Count
from blog.models import Comment, Post, Tag


def get_related_posts_count(tag):
    return tag.posts.count()


def get_comments_count(posts):
    posts_ids = [post.id for post in posts]
    filtered_posts = Post.objects.filter(id__in=posts_ids)
    posts_with_comments = filtered_posts.annotate(
        num_comments=Count("comments")
    )
    ids_and_comments = posts_with_comments.values_list("id", "num_comments")
    count_for_id = dict(ids_and_comments)
    for post in posts:
        post.num_comments = count_for_id[post.id]


def serialize_post(post):
    return {
        "title": post.title,
        "teaser_text": post.text[:200],
        "author": post.author.username,
        "comments_amount": len(Comment.objects.filter(post=post)),
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_post_optimised(post):
    return {
        "title": post.title,
        "teaser_text": post.text[:200],
        "author": post.author.username,
        "comments_amount": post.num_comments,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': len(Post.objects.filter(tags=tag)),
    }


def index(request):
    posts = Post.objects.all().prefetch_related('author')
    posts_with_num_likes = posts.annotate(num_likes=Count('likes'))
    most_popular_posts = posts_with_num_likes.order_by('-num_likes')[:5]
    most_fresh_posts = posts.order_by('-published_at')[:5]
    get_comments_count(most_popular_posts)
    get_comments_count(most_fresh_posts)
    tags_num_posts_annotated = Tag.objects.annotate(num_posts=Count('posts'))
    most_popular_tags = tags_num_posts_annotated.order_by('-num_posts')[:5]

    context = {
        'most_popular_posts': [serialize_post_optimised(post) for post in most_popular_posts],
        'page_posts': [serialize_post_optimised(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)
    comments = Comment.objects.filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.all()

    serialized_post = {
        "title": post.title,
        "text": post.text,
        "author": post.author.username,
        "comments": serialized_comments,
        'likes_amount': len(likes),
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in related_tags],
    }

    all_tags = Tag.objects.all()
    popular_tags = sorted(all_tags, key=get_related_posts_count)
    most_popular_tags = popular_tags[-5:]

    most_popular_posts = []  # TODO. Как это посчитать?

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post_optimised(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    all_tags = Tag.objects.all()
    popular_tags = sorted(all_tags, key=get_related_posts_count)
    most_popular_tags = popular_tags[-5:]

    most_popular_posts = []  # TODO. Как это посчитать?

    related_posts = tag.posts.all()[:20]
    related_annotated_posts = related_posts.annotate(
        num_likes=Count('likes', distinct=True),
        num_comments=Count('comments', distinct=True),
    )

    context = {
        "tag": tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post_optimised(post) for post in related_annotated_posts],
        'most_popular_posts': [serialize_post_optimised(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
