// Store tea data for reference
let teaData = {};

function displayNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease-in;
        max-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function updateStockDisplay(teaId, newStock) {
    // Find all stock displays for this tea and update them
    const stockElements = document.querySelectorAll(`[data-tea-id="${teaId}"]`);
    stockElements.forEach(element => {
        const card = element.closest('.tea-card');
        if (card) {
            const stockDiv = card.querySelector('.tea-card-stock');
            if (stockDiv) {
                stockDiv.textContent = `Stock: ${newStock}`;
                // Add animation
                stockDiv.style.transition = 'color 0.3s ease';
                stockDiv.style.color = '#ff9800';
                setTimeout(() => {
                    stockDiv.style.color = '#999';
                }, 500);
            }
        }
    });
}

async function addToCartWithNotification(teaId, teaName, quantity = 1) {
    const token = localStorage.getItem('token');
    
    if (token) {
        // Use backend API if logged in
        try {
            const response = await fetch('http://localhost:8000/api/cart/add/', {
                method: 'POST',
                headers: {
                    'Authorization': `Token ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tea_id: teaId, quantity: quantity })
            });
            
            if (response.ok) {
                const backendCart = await response.json();
                
                // Update frontend cart with backend data
                syncLocalCartWithBackend(backendCart);
                
                // Get updated tea data
                const teaResponse = await fetch(`http://localhost:8000/api/teas/${teaId}/`, {
                    headers: {
                        'Authorization': `Token ${token}`,
                        'Content-Type': 'application/json',
                    }
                });
                
                if (teaResponse.ok) {
                    const updatedTea = await teaResponse.json();
                    teaData[teaId] = updatedTea;
                    
                    // Update stock display
                    updateStockDisplay(teaId, updatedTea.quantity_in_stock);
                    
                    // Show success message
                    displayNotification(`✓ Added ${quantity} × ${teaName} to cart`, 'success');
                    updateCartCounter();
                    return;
                }
            } else {
                const error = await response.json();
                displayNotification(`Error: ${error.error || 'Could not add to cart'}`, 'error');
                return;
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            displayNotification('Error adding to cart', 'error');
        }
    }
    
    // Fallback: use localStorage
    const teaInCart = cart.find(item => item.teaId === teaId);
    if (teaInCart) {
        teaInCart.quantity += quantity;
    } else {
        cart.push({ teaId: teaId, quantity: quantity });
    }
    saveCart();
    
    // Update local stock display
    if (teaData[teaId]) {
        teaData[teaId].quantity_in_stock -= quantity;
        updateStockDisplay(teaId, teaData[teaId].quantity_in_stock);
    }
    
    displayNotification(`✓ Added ${quantity} × ${teaName} to cart`, 'success');
    updateCartCounter();
}

function syncLocalCartWithBackend(backendCart) {
    cart = [];
    if (backendCart.items) {
        backendCart.items.forEach(item => {
            cart.push({
                teaId: item.tea.id,
                quantity: item.quantity,
                cartItemId: item.id
            });
        });
    }
    saveCart();
}

function getAuthHeaders() {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }
    return headers;
}
