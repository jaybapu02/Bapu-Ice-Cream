import re
from django.templatetags.static import static

EXACT_NAME_MAP = {
    'vanilla classic': 'Vanilla Classic.avif',
    'chocolate delight': 'Chocolate Delight.png',
    'strawberry bliss': 'Strawberry Bliss.jpg',
    'mango magic': 'Mango Magic.avif',
    'kesar pista royal': 'Kesar-Pista-Ice-Cream.png',
    'butterscotch crunch': 'Butterscotch-Crunch-Cake.jpg',
    'coffee mocha': 'Coffee Mocha.jpg',
    'black currant twist': 'black currant twist.jpg',
    'cookies & cream': 'Cookies & Cream.jpg',
    'dry fruit special': 'Dry Fruit Special.png',
    'tender coconut fresh': 'Tender Coconut Fresh.jpg',
    'rainbow fantasy': 'Rainbow Fantasy.avif',
}

KEYWORD_MAP = [
    (r'\bvanilla\b', 'Vanilla Classic.avif'),
    (r'\bchocolate\b', 'Chocolate Delight.png'),
    (r'\bstrawberry\b', 'Strawberry Bliss.jpg'),
    (r'\bmango\b', 'Mango Magic.avif'),
    (r'\bpista\b|\bkesar\b|\bpistachio\b', 'Kesar-Pista-Ice-Cream.png'),
    (r'\bbutterscotch\b|\bbutter\b', 'Butterscotch-Crunch-Cake.jpg'),
    (r'\bcoffee\b|\bmocha\b', 'Coffee Mocha.jpg'),
    (r'\bblack\b|\bcurrant\b|\bberry\b', 'black currant twist.jpg'),
    (r'\bcookie\b|\bcookies\b|\bcream\b', 'Cookies & Cream.jpg'),
    (r'\bdry\b|\bnut\b|\bnuts\b|\bfruit\b', 'Dry Fruit Special.png'),
    (r'\bcoconut\b|\btender\b', 'Tender Coconut Fresh.jpg'),
    (r'\brainbow\b|\bfantasy\b|\bcolorful\b', 'Rainbow Fantasy.avif'),
]

CATEGORY_MAP = [
    (r'\bclassic\b', 'Vanilla Classic.avif'),
    (r'\bpremium\b', 'Butterscotch-Crunch-Cake.jpg'),
    (r'\bseasonal\b', 'Mango Magic.avif'),
]

FALLBACK_POOL = [
    'Vanilla Classic.avif', 'Chocolate Delight.png', 'Strawberry Bliss.jpg', 'Mango Magic.avif',
    'Kesar-Pista-Ice-Cream.png', 'Butterscotch-Crunch-Cake.jpg', 'Coffee Mocha.jpg',
    'black currant twist.jpg', 'Cookies & Cream.jpg', 'Dry Fruit Special.png',
    'Tender Coconut Fresh.jpg', 'Rainbow Fantasy.avif',
]

EXTERNAL_IMAGES = {
    'vanilla': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&q=80',
    'chocolate': 'https://images.unsplash.com/photo-1570197785657-d9fe21bf7a0f?w=600&q=80',
    'strawberry': 'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600&q=80',
    'mango': 'https://images.unsplash.com/photo-1560008581-09826d1de69e?w=600&q=80',
    'pista': 'https://images.unsplash.com/photo-1505394033641-40f1ad5e3bb1?w=600&q=80',
    'butterscotch': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=600&q=80',
    'coffee': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=600&q=80',
    'black currant': 'https://images.unsplash.com/photo-1570197785657-d9fe21bf7a0f?w=600&q=80',
    'cookies cream': 'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&q=80',
    'dry fruit': 'https://images.unsplash.com/photo-1505394033641-40f1ad5e3bb1?w=600&q=80',
    'coconut': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&q=80',
    'rainbow': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=600&q=80',
}

EXTERNAL_FALLBACKS = [
    'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&q=80',
    'https://images.unsplash.com/photo-1570197785657-d9fe21bf7a0f?w=600&q=80',
    'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600&q=80',
    'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=600&q=80',
    'https://images.unsplash.com/photo-1560008581-09826d1de69e?w=600&q=80',
    'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&q=80',
    'https://images.unsplash.com/photo-1505394033641-40f1ad5e3bb1?w=600&q=80',
]


def get_display_image(product):
    """Return the best image URL for a product.
    
    Priority:
    1. Product's own uploaded image (DB)
    2. Exact name match in local static
    3. Keyword match in product name
    4. Category-based match
    5. Deterministic fallback from local pool
    6. External URL fallback
    """
    if product.image:
        return product.image.url

    name_lower = product.name.lower().strip()
    cat_lower = product.category.name.lower().strip() if product.category else ''

    if name_lower in EXACT_NAME_MAP:
        return static(EXACT_NAME_MAP[name_lower])

    for pattern, img in KEYWORD_MAP:
        if re.search(pattern, name_lower):
            return static(img)

    for pattern, img in CATEGORY_MAP:
        if re.search(pattern, cat_lower):
            return static(img)

    idx = hash(product.name) % len(FALLBACK_POOL)
    return static(FALLBACK_POOL[idx])


def get_external_image(product, use_external=False):
    """Return an external high-quality image URL for a product.
    Used as last resort when no local image matches well.
    """
    name_lower = product.name.lower().strip()

    for key, url in EXTERNAL_IMAGES.items():
        if key in name_lower:
            return url

    idx = hash(product.name) % len(EXTERNAL_FALLBACKS)
    return EXTERNAL_FALLBACKS[idx]


def annotate_products_with_images(products, prefer_external=False):
    """Add a display_image attribute to each product in the queryset."""
    for product in products:
        product.display_image = get_display_image(product)
    return products
