// Backend API Cart Management Functions
// These functions interact with the backend cart endpoints

async function getBackendCart() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch('https://tjib26.pythonanywhere.com/api/cart/', {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const cart = await response.json();
            console.log('Backend cart fetched:', cart);
            return cart;
        }
    } catch (error) {
        console.error('Failed to fetch cart from backend:', error);
    }
    return null;
}

async function addToBackendCart(teaId, quantity = 1) {
    const token = localStorage.getItem('token');
    if (!token) {
        console.log('User not logged in - using localStorage cart only');
        return null;
    }
    
    try {
        const response = await fetch('https://tjib26.pythonanywhere.com/api/cart/add/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ tea_id: teaId, quantity: quantity })
        });
        if (response.ok) {
            const cart = await response.json();
            console.log('Added to backend cart:', cart);
            return cart;
        } else {
            const error = await response.json();
            console.error('Error adding to cart:', error);
            alert('Error: ' + (error.error || 'Could not add to cart'));
            return null;
        }
    } catch (error) {
        console.error('Failed to add to backend cart:', error);
    }
    return null;
}

async function updateBackendCartItem(cartItemId, quantity) {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch('https://tjib26.pythonanywhere.com/api/cart/update/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ cart_item_id: cartItemId, quantity: quantity })
        });
        if (response.ok) {
            const cart = await response.json();
            console.log('Updated backend cart item:', cart);
            return cart;
        } else {
            const error = await response.json();
            console.error('Error updating cart:', error);
            alert('Error: ' + (error.error || 'Could not update cart'));
            return null;
        }
    } catch (error) {
        console.error('Failed to update backend cart item:', error);
    }
    return null;
}

async function removeFromBackendCart(cartItemId) {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch('https://tjib26.pythonanywhere.com/api/cart/remove/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ cart_item_id: cartItemId })
        });
        if (response.ok) {
            const cart = await response.json();
            console.log('Removed from backend cart:', cart);
            return cart;
        } else {
            const error = await response.json();
            console.error('Error removing from cart:', error);
            alert('Error: ' + (error.error || 'Could not remove from cart'));
            return null;
        }
    } catch (error) {
        console.error('Failed to remove from backend cart:', error);
    }
    return null;
}

async function clearBackendCart() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch('https://tjib26.pythonanywhere.com/api/cart/clear/', {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const cart = await response.json();
            console.log('Backend cart cleared:', cart);
            return cart;
        } else {
            const error = await response.json();
            console.error('Error clearing cart:', error);
            return null;
        }
    } catch (error) {
        console.error('Failed to clear backend cart:', error);
    }
    return null;
}

// Updated addToCart function that uses backend if user is logged in
async function addToCartWithSync(teaId, quantity = 1) {
    const token = localStorage.getItem('token');
    
    // If user is logged in, use backend
    if (token) {
        const backendCart = await addToBackendCart(teaId, quantity);
        if (backendCart) {
            // Sync frontend cart with backend
            syncLocalCartWithBackend(backendCart);
            updateCartCounter();
            return;
        }
    }
    
    // Fallback to localStorage
    const teaInCart = cart.find(item => item.teaId === teaId);
    if (teaInCart) {
        teaInCart.quantity += quantity;
    } else {
        cart.push({ teaId: teaId, quantity: quantity });
    }
    saveCart();
}

function syncLocalCartWithBackend(backendCart) {
    // Convert backend cart format to local format
    // Backend cart has: { id, user, created_at, items: [{id, cart, tea, quantity}, ...] }
    cart = [];
    if (backendCart.items) {
        backendCart.items.forEach(item => {
            cart.push({
                teaId: item.tea.id,
                quantity: item.quantity,
                cartItemId: item.id  // Store backend ID for updates
            });
        });
    }
    saveCart();
}
