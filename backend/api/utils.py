from django.db.models import Sum

from recipes.models import RecipeIngredient, ShoppingCart


def generate_shopping_list(user):
    """Генерирует содержимое файла списка покупок"""
    user_cart = ShoppingCart.objects.filter(user=user)
    recipes = [cart.recipe for cart in user_cart]

    if not recipes:
        return None

    ingredients = RecipeIngredient.objects.filter(
        recipe__in=recipes
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('ingredient__name')

    shopping_list = []
    shopping_list.append("Foodgram - Список покупок")
    shopping_list.append("=" * 40)
    shopping_list.append("")

    for idx, ingredient in enumerate(ingredients, 1):
        name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['total_amount']
        shopping_list.append(f"{idx}. {name} - {amount} {unit}")

    shopping_list.append("")
    shopping_list.append("=" * 40)
    shopping_list.append(f"Всего позиций: {len(ingredients)}")
    shopping_list.append(f"Рецептов: {len(recipes)}")
    shopping_list.append("")
    shopping_list.append("Приятных покупок!")

    return '\n'.join(shopping_list)
