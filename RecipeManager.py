import streamlit as st
import requests
from typing import List, Dict, Optional

# API Configuration
API_KEY = "328993ee5d0743ca8cfdc2a53f79f93a"
BASE_URL = "https://api.spoonacular.com/recipes"

class FavoriteRecipesCollection:
    """Abstract Data Type (ADT) for managing favorite recipes collection"""
    
    def __init__(self):
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []
    
    def add(self, recipe: Dict) -> bool:
        """Add recipe to collection"""
        if not self.contains(recipe['id']):
            compact_recipe = {
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'readyInMinutes': recipe['readyInMinutes'],
                'servings': recipe['servings'],
                'sourceUrl': recipe.get('sourceUrl', '')
            }
            st.session_state.favorites.append(compact_recipe)
            return True
        return False
    
    def remove(self, recipe_id: int) -> bool:
        """Remove recipe from collection"""
        initial_count = len(st.session_state.favorites)
        st.session_state.favorites = [r for r in st.session_state.favorites if r['id'] != recipe_id]
        return len(st.session_state.favorites) < initial_count
    
    def contains(self, recipe_id: int) -> bool:
        """Check if recipe exists in collection"""
        return any(r['id'] == recipe_id for r in st.session_state.favorites)
    
    def get_all(self) -> List[Dict]:
        """Get all recipes in collection"""
        return st.session_state.favorites.copy()
    
    def get_by_id(self, recipe_id: int) -> Optional[Dict]:
        """Find recipe by ID"""
        for recipe in st.session_state.favorites:
            if recipe['id'] == recipe_id:
                return recipe
        return None
    
    def count(self) -> int:
        """Get total number of recipes in collection"""
        return len(st.session_state.favorites)
    
    def clear(self) -> None:
        """Clear the collection"""
        st.session_state.favorites = []

# Initialize ADT
favorites = FavoriteRecipesCollection()

def display_recipe_card(recipe: Dict) -> None:
    """Display recipe card component"""
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(recipe.get('image', ''), width=150)
        
        with col2:
            st.subheader(recipe['title'])
            st.caption(f"⏱️ {recipe['readyInMinutes']} min | 🍽️ {recipe['servings']} servings")
            
            # Favorite management
            if favorites.contains(recipe['id']):
                if st.button("❤️ Remove from favorites", key=f"unfav_{recipe['id']}"):
                    favorites.remove(recipe['id'])
                    st.rerun()
            else:
                if st.button("♡ Add to favorites", key=f"fav_{recipe['id']}"):
                    favorites.add(recipe)
                    st.rerun()
            
            # Details button
            if st.button("🔍 View details", key=f"details_{recipe['id']}"):
                st.session_state.selected_recipe_id = recipe['id']
                st.rerun()

def display_favorites_page() -> None:
    """Favorites page view"""
    st.subheader("❤️ My Favorite Recipes")
    
    if favorites.count() == 0:
        st.info("Your favorites list is empty")
        return
    
    # Filtering and sorting
    with st.expander("Filters and sorting"):
        search_query = st.text_input("Search by name")
        sort_option = st.selectbox("Sort by", 
                                 ["Date added", "Cooking time", "Name"])
    
    # Apply filters
    filtered = favorites.get_all()
    
    if search_query:
        filtered = [r for r in filtered if search_query.lower() in r['title'].lower()]
    
    if sort_option == "Cooking time":
        filtered.sort(key=lambda x: x['readyInMinutes'])
    elif sort_option == "Name":
        filtered.sort(key=lambda x: x['title'])
    
    # Display results
    if not filtered:
        st.warning("No recipes found")
    else:
        for recipe in filtered:
            display_recipe_card(recipe)

def display_recipe_details(recipe_id: int) -> None:
    """Recipe details page view"""
    recipe = get_recipe_details(recipe_id)
    if not recipe:
        st.error("Recipe not found")
        return
    
    st.button("← Back", on_click=lambda: st.session_state.pop('selected_recipe_id'))
    
    # Header with favorite controls
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(recipe['title'])
    with col2:
        if favorites.contains(recipe_id):
            if st.button("❤️ Remove from favorites", use_container_width=True):
                favorites.remove(recipe_id)
                st.rerun()
        else:
            if st.button("♡ Add to favorites", use_container_width=True):
                favorites.add(recipe)
                st.rerun()
    
    # Main content
    st.image(recipe.get('image', ''), width=400)
    
    with st.expander("📝 Ingredients"):
        for ing in recipe['extendedIngredients']:
            st.markdown(f"- {ing['original']}")
    
    with st.expander("📋 Instructions"):
        if recipe['instructions']:
            instructions = recipe['instructions'].replace('<ol>', '').replace('</ol>', '').replace('<li>', '1. ')
            st.markdown(instructions)
        else:
            st.warning("No instructions available")
    
    if recipe.get('sourceUrl'):
        st.markdown(f"[🔗 Original recipe]({recipe['sourceUrl']})")

# Main app interface
st.set_page_config(page_title="Cooking Assistant", layout="wide")

# Navigation sidebar
page = st.sidebar.radio("Menu", ["Recipe Search", "My Favorites", "About"])

if page == "Recipe Search":
    st.title("🔍 Recipe Search")
    
    with st.form("search_form"):
        query = st.text_input("Recipe name")
        ingredients = st.text_input("Ingredients (comma separated)")
        submitted = st.form_submit_button("Search")
    
    if submitted:
        if not query and not ingredients:
            st.warning("Please enter search criteria")
        else:
            results = search_recipes(query, ingredients)
            if results:
                for recipe in results:
                    display_recipe_card(recipe)
            else:
                st.info("No recipes found")

elif page == "My Favorites":
    display_favorites_page()

elif page == "About":
    st.title("ℹ️ About")
    st.write("""
    ### Cooking Assistant
    Recipe search and management app using Spoonacular API.
    
    Features:
    - Search recipes by name and ingredients
    - Save favorite recipes
    - Filter and sort favorites
    """)

# Handle recipe details view
if 'selected_recipe_id' in st.session_state:
    display_recipe_details(st.session_state.selected_recipe_id)