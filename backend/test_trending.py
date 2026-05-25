import requests

try:
    res = requests.get('http://localhost:8000/api/trending/homepage')
    data = res.json()
    print('Trending Now (first 5):')
    for p in data['sections']['trending_now']['products'][:5]:
        print(f"  {p['product_name']} - Score: {p['score']}")
    
    print('\nPopular Today (first 5):')
    for p in data['sections']['popular_today']['products'][:5]:
        print(f"  {p['product_name']} - Score: {p['score']}")
except Exception as e:
    print('Failed:', e)
