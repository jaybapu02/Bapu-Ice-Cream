from django.db import migrations


def seed_services(apps, schema_editor):
    ServiceCategory = apps.get_model('home', 'ServiceCategory')
    Service = apps.get_model('home', 'Service')

    # ── Categories ──
    cats = {
        'home-delivery': ServiceCategory.objects.create(
            name='Home Delivery', slug='home-delivery',
            description='Get your favourite ice cream delivered straight to your door.',
            icon='bi-truck'
        ),
        'catering': ServiceCategory.objects.create(
            name='Catering', slug='catering',
            description='Full-service ice cream catering for any occasion.',
            icon='bi-cup-straw'
        ),
        'events': ServiceCategory.objects.create(
            name='Events', slug='events',
            description='Make your celebrations unforgettable with our event services.',
            icon='bi-calendar-event'
        ),
        'wholesale': ServiceCategory.objects.create(
            name='Wholesale', slug='wholesale',
            description='Bulk orders and custom solutions for businesses.',
            icon='bi-box-seam'
        ),
    }

    # ── Services ──
    services_data = [
        {
            'title': 'Home Delivery',
            'slug': 'home-delivery',
            'category': 'home-delivery',
            'short_description': 'Craving ice cream at home? Get your favourite flavours delivered fresh to your doorstep. Free delivery on orders above ₹200.',
            'full_description': 'Enjoy Bapu Ice Cream from the comfort of your home. Our home delivery service brings handcrafted ice cream straight to your door. Simply browse our menu, place your order, and we\'ll handle the rest. Free delivery on orders above ₹200, with same-day delivery available within city limits. Order by 4 PM for evening delivery.',
            'icon': 'bi-truck',
            'price': None,
            'is_featured': True,
            'is_popular': True,
            'is_active': True,
            'sort_order': 1,
            'cta_text': 'Order Now',
            'cta_url': '/order/',
        },
        {
            'title': 'Ice Cream Catering',
            'slug': 'ice-cream-catering',
            'category': 'catering',
            'short_description': 'Full-service ice cream catering for parties, gatherings, and special events. We bring the cart, you bring the guests.',
            'full_description': 'Our ice cream catering service is perfect for any event. We arrive with a professionally stocked cart, a variety of flavours, and all the toppings. Guests can build their own sundaes, cones, or cups. We handle setup, service, and cleanup so you can focus on your guests. Minimum order of 50 servings.',
            'icon': 'bi-cup-straw',
            'price': '2499',
            'is_featured': True,
            'is_popular': True,
            'is_active': True,
            'sort_order': 2,
            'cta_text': 'Book Catering',
            'cta_url': '/catering/',
        },
        {
            'title': 'Birthday Party Catering',
            'slug': 'birthday-party-catering',
            'category': 'events',
            'short_description': 'Make birthdays extra special with our dedicated party packages — from ice cream cakes to custom toppings bars.',
            'full_description': 'Celebrate your birthday with Bapu Ice Cream! Our birthday party package includes a selection of premium ice creams, a custom ice cream cake, a toppings bar, and party favours. We can also personalize the menu to match your party theme. Available for kids and adults. Includes a dedicated server for the duration of your event.',
            'icon': 'bi-gift',
            'price': '3499',
            'is_featured': False,
            'is_popular': True,
            'is_active': True,
            'sort_order': 3,
            'cta_text': 'Book Now',
            'cta_url': '/catering/',
        },
        {
            'title': 'Wedding & Event Catering',
            'slug': 'wedding-event-catering',
            'category': 'events',
            'short_description': 'Elegant ice cream catering for weddings, receptions, engagements, and milestone celebrations.',
            'full_description': 'Make your special day even sweeter with our premium wedding and event catering. We offer elegant ice cream buffets, custom flavours to match your theme, ice cream towers, and dessert bars. Our team works closely with your wedding planner to ensure seamless coordination. Tastings available upon request.',
            'icon': 'bi-heart',
            'price': '6999',
            'is_featured': True,
            'is_popular': False,
            'is_active': True,
            'sort_order': 4,
            'cta_text': 'Enquire Now',
            'cta_url': '/catering/',
        },
        {
            'title': 'Corporate Event Catering',
            'slug': 'corporate-event-catering',
            'category': 'catering',
            'short_description': 'Impress your team and clients with professional ice cream catering for office events, conferences, and team building.',
            'full_description': 'Elevate your corporate events with Bapu Ice Cream catering. We cater to office parties, team-building events, client meetings, product launches, and company anniversaries. Choose from our curated corporate packages or build a custom menu. We offer contactless serving options and branded ice cream cups for a professional touch.',
            'icon': 'bi-briefcase',
            'price': '4999',
            'is_featured': False,
            'is_popular': False,
            'is_active': True,
            'sort_order': 5,
            'cta_text': 'Get Quote',
            'cta_url': '/catering/',
        },
        {
            'title': 'Bulk Ice Cream Orders',
            'slug': 'bulk-ice-cream-orders',
            'category': 'wholesale',
            'short_description': 'Need ice cream in bulk? We supply large quantities for resellers, events, and institutions at wholesale prices.',
            'full_description': 'Perfect for retailers, restaurants, hotels, and event organizers. Our bulk ordering service offers competitive wholesale pricing on our full range of flavours. Orders available in 1L, 2L, and 5L tubs. Minimum order quantity applies. Custom labelling available for orders above 100 units. Free delivery within city limits on orders above ₹5000.',
            'icon': 'bi-box-seam',
            'price': '999',
            'is_featured': False,
            'is_popular': True,
            'is_active': True,
            'sort_order': 6,
            'cta_text': 'Order Bulk',
            'cta_url': '/order/',
        },
        {
            'title': 'Custom Ice Cream Orders',
            'slug': 'custom-ice-cream-orders',
            'category': 'wholesale',
            'short_description': 'Create your own flavour! Choose your base, mix-ins, and packaging for a truly unique ice cream experience.',
            'full_description': 'Dreaming of a flavour that doesn\'t exist yet? We\'ll make it for you. Our custom ice cream service lets you choose the base (vanilla, chocolate, mango, or kulfi), select your mix-ins (nuts, fruits, candies, cookies), pick a packaging style, and even name your creation. Minimum order of 10L. Perfect for weddings, brand launches, and special promotions.',
            'icon': 'bi-palette',
            'price': '1499',
            'is_featured': False,
            'is_popular': False,
            'is_active': True,
            'sort_order': 7,
            'cta_text': 'Create Flavour',
            'cta_url': '/order/',
        },
        {
            'title': 'Party Packages',
            'slug': 'party-packages',
            'category': 'events',
            'short_description': 'All-in-one party packages combining ice cream, toppings, cakes, and decorations for hassle-free celebrations.',
            'full_description': 'Our Party Packages take the stress out of event planning. Choose from Silver, Gold, or Platinum tiers — each including a curated selection of ice creams, toppings, cones, cups, napkins, and decorations. Upgrade to include an ice cream cake, custom banner, and a dedicated server. Packages available for 10, 20, 30, 50, or 100 guests.',
            'icon': 'bi-stars',
            'price': '1999',
            'is_featured': True,
            'is_popular': True,
            'is_active': True,
            'sort_order': 8,
            'cta_text': 'View Packages',
            'cta_url': '/catering/',
        },
    ]

    for data in services_data:
        cat_key = data.pop('category')
        Service.objects.create(category=cats[cat_key], **data)


def reverse_seed(apps, schema_editor):
    Service = apps.get_model('home', 'Service')
    ServiceCategory = apps.get_model('home', 'ServiceCategory')
    Service.objects.all().delete()
    ServiceCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0010_servicecategory_service_servicefaq_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_services, reverse_seed),
    ]
