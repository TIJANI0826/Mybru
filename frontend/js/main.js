// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {

    // Store tea data for reference
    let teaData = {};

    // ============ NOTIFICATION SYSTEM ============
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
                    stockDiv.setAttribute('data-stock', newStock);
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

    const userMenu = document.getElementById('user-menu');
    const authLinks = document.getElementById('auth-links');
    const userNameSpan = document.getElementById('user-name');
    const logoutBtn = document.getElementById('logout-btn');

    function checkAuthStatus() {
        const user = JSON.parse(localStorage.getItem('user'));
        const token = localStorage.getItem('token');

        if (user && token) {
            // User is logged in
            authLinks.style.display = 'none';
            userMenu.style.display = 'flex';
            userNameSpan.textContent = user.username || user.email;
        } else {
            // User is not logged in
            authLinks.style.display = 'flex';
            userMenu.style.display = 'none';
        }
    }

    function logout() {
        const token = localStorage.getItem('token');
        const API_URL = 'http://localhost:8000/api';

        if (token) {
            // Call logout endpoint to invalidate token on backend
            fetch(`${API_URL}/auth/logout/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Token ${token}`,
                    'Content-Type': 'application/json',
                }
            }).then(response => {
                if (response.ok) {
                    // Clear localStorage
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    
                    // Update UI
                    checkAuthStatus();
                    
                    // Redirect to home
                    window.location.href = 'home.html';
                }
            }).catch(error => {
                console.error('Logout error:', error);
                // Still clear local storage and redirect even if backend fails
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                checkAuthStatus();
                window.location.href = 'home.html';
            });
        }
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Check auth status on page load
    checkAuthStatus();

    // Mobile nav toggle: find the toggle and wire up open/close behavior
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            const expanded = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', String(!expanded));
            document.body.classList.toggle('nav-open');
        });

        // Close menu when clicking any link inside it
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                document.body.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.site-nav') && document.body.classList.contains('nav-open')) {
                document.body.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // ============ SHOPPING CART & OTHER SECTIONS ============

    // Get elements that might be on generic.html
    const teaGalleryContainer = document.getElementById('tea-gallery-container');
    const teaGallerySection = document.getElementById('tea-gallery-section');

    // Get elements that might be on cart.html
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartTotalSpan = document.getElementById('cart-total');

    // Get elements that might be on checkout.html
    const checkoutCartItems = document.getElementById('checkout-cart-items');
    const checkoutSubtotalSpan = document.getElementById('checkout-subtotal');
    const deliveryOptions = document.getElementById('delivery-options');
    const pickupLocationDiv = document.getElementById('pickup-location');
    const deliveryAddressDiv = document.getElementById('delivery-address');
    const deliveryFeeSpan = document.getElementById('delivery-fee');
    const finalOrderTotalSpan = document.getElementById('final-order-total');
    const placeOrderBtn = document.getElementById('place-order-btn');

    // Global elements
    const cartCounter = document.getElementById('cart-counter');

    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const DELIVERY_FEE = 5.00; // Example fixed delivery fee

    function updateCartCounter() {
        if (cartCounter) {
            cartCounter.textContent = cart.reduce((acc, item) => acc + item.quantity, 0);
        }
    }

    function saveCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCounter();
    }

    function addToCart(teaId) {
        const teaInCart = cart.find(item => item.teaId === teaId);
        if (teaInCart) {
            teaInCart.quantity++;
        } else {
            cart.push({ teaId: teaId, quantity: 1 });
        }
        saveCart();
    }

    async function updateQuantity(teaId, newQuantity) {
        const cartItem = cart.find(item => item.teaId === teaId);
        if (!cartItem) return;

        const oldQuantity = cartItem.quantity;
        const token = localStorage.getItem('token');

        // If user is authenticated and we have a backend cartItem id, call backend to update
        if (token && cartItem.cartItemId) {
            try {
                const response = await fetch(`${API_URL}/cart/update/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Token ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ cart_item_id: cartItem.cartItemId, quantity: newQuantity })
                });

                if (response.ok) {
                    const backendCart = await response.json();
                    syncLocalCartWithBackend(backendCart);

                    // Refresh tea info for this tea to get updated stock
                    try {
                        const teaResp = await fetch(`${API_URL}/teas/${teaId}/`, { headers: getAuthHeaders() });
                        if (teaResp.ok) {
                            const updatedTea = await teaResp.json();
                            teaData[teaId] = updatedTea;
                            updateStockDisplay(teaId, updatedTea.quantity_in_stock);
                        }
                    } catch (err) {
                        console.error('Failed to refresh tea after update:', err);
                    }
                } else {
                    const err = await response.json();
                    displayNotification(`Error: ${err.error || 'Could not update cart'}`, 'error');
                }
            } catch (error) {
                console.error('Error updating cart item:', error);
                displayNotification('Error updating cart', 'error');
            }

        } else {
            // Local (guest) flow: adjust local stock based on quantity difference
            const delta = newQuantity - oldQuantity; // positive -> increase in cart, reduce stock
            if (delta > 0) {
                if (teaData[teaId]) {
                    if (teaData[teaId].quantity_in_stock < delta) {
                        displayNotification('Not enough stock', 'error');
                        return;
                    }
                    teaData[teaId].quantity_in_stock -= delta;
                    updateStockDisplay(teaId, teaData[teaId].quantity_in_stock);
                }
            } else if (delta < 0) {
                // restoring stock
                if (teaData[teaId]) {
                    teaData[teaId].quantity_in_stock += Math.abs(delta);
                    updateStockDisplay(teaId, teaData[teaId].quantity_in_stock);
                }
            }

            // Update or remove local cart item
            cartItem.quantity = newQuantity;
            if (cartItem.quantity <= 0) {
                cart = cart.filter(item => item.teaId !== teaId);
            }
            saveCart();
        }

        if (window.location.pathname.includes('cart.html')) {
            renderCartPage();
        }
    }

    async function removeItem(teaId) {
        const cartItem = cart.find(item => item.teaId === teaId);
        if (!cartItem) return;

        const token = localStorage.getItem('token');

        if (token && cartItem.cartItemId) {
            try {
                const response = await fetch(`${API_URL}/cart/remove/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Token ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ cart_item_id: cartItem.cartItemId })
                });

                if (response.ok) {
                    const backendCart = await response.json();
                    syncLocalCartWithBackend(backendCart);

                    // Refresh tea info to reflect restored stock
                    try {
                        const teaResp = await fetch(`${API_URL}/teas/${teaId}/`, { headers: getAuthHeaders() });
                        if (teaResp.ok) {
                            const updatedTea = await teaResp.json();
                            teaData[teaId] = updatedTea;
                            updateStockDisplay(teaId, updatedTea.quantity_in_stock);
                        }
                    } catch (err) {
                        console.error('Failed to refresh tea after remove:', err);
                    }
                } else {
                    const err = await response.json();
                    displayNotification(`Error: ${err.error || 'Could not remove from cart'}`, 'error');
                }
            } catch (error) {
                console.error('Error removing cart item:', error);
                displayNotification('Error removing item from cart', 'error');
            }
        } else {
            // Local fallback: restore stock locally
            if (teaData[teaId]) {
                teaData[teaId].quantity_in_stock += cartItem.quantity;
                updateStockDisplay(teaId, teaData[teaId].quantity_in_stock);
            }

            cart = cart.filter(item => item.teaId !== teaId);
            saveCart();
        }

        if (window.location.pathname.includes('cart.html')) {
            renderCartPage();
        }
    }

    const API_URL = 'http://localhost:8000/api';

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

    async function addToCartWithNotification(teaId, teaName, quantity = 1) {
        const token = localStorage.getItem('token');
        
        if (token) {
            // Use backend API if logged in
            try {
                const response = await fetch(`${API_URL}/cart/add/`, {
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
                    const teaResponse = await fetch(`${API_URL}/teas/${teaId}/`, {
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

    async function fetchTeaDetails(teaId) {
        try {
            const response = await fetch(`${API_URL}/teas/${teaId}/`, {
                headers: getAuthHeaders()
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return await response.json();
        } catch (error) {
            console.error(`Failed to fetch tea details for ID ${teaId}:`, error);
            return null;
        }
    }

    async function fetchTeas() {
        try {
            const response = await fetch(`${API_URL}/teas/`, {
                headers: getAuthHeaders()
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const teas = await response.json();
            displayTeas(teas);
        } catch (error) {
            console.error('Failed to fetch teas:', error);
            if (teaGalleryContainer) {
                teaGalleryContainer.innerHTML = '<p>Failed to load teas. Please try again later.</p>';
            }
        }
    }

    function displayTeas(teas) {
        if (!teaGalleryContainer) return;
        teaGalleryContainer.innerHTML = '';
        teas.forEach(tea => {
            const teaCard = document.createElement('div');
            teaCard.classList.add('tea-card');
            teaCard.innerHTML = `
                <div class="tea-card-image">
                    <img src="https://via.placeholder.com/200x200" alt="${tea.name}">
                </div>
                <div class="tea-card-content">
                    <h4>${tea.name}</h4>
                    <p>${tea.description}</p>
                    <div class="tea-card-footer">
                        <div class="tea-card-price">$${tea.price}</div>
                        <div class="tea-card-stock" data-stock="${tea.quantity_in_stock}">Stock: ${tea.quantity_in_stock}</div>
                    </div>
                    <button class="add-to-cart-btn" data-tea-id="${tea.id}" data-tea-name="${tea.name}">Add to Cart</button>
                </div>
            `;
            teaGalleryContainer.appendChild(teaCard);
            
            // Store tea data globally for later reference
            teaData[tea.id] = tea;
        });

        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                const teaId = parseInt(event.target.getAttribute('data-tea-id'));
                const teaName = event.target.getAttribute('data-tea-name');
                
                // Disable button during operation
                event.target.disabled = true;
                event.target.textContent = 'Adding...';
                
                await addToCartWithNotification(teaId, teaName, 1);
                
                // Re-enable button
                event.target.disabled = false;
                event.target.textContent = 'Add to Cart';
            });
        });
    }

    async function renderCartPage() {
        if (!cartItemsContainer) return; // Only run on cart page

        cartItemsContainer.innerHTML = '';
        let total = 0;

        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
            cartTotalSpan.textContent = '0.00';
            return;
        }

        for (const cartItem of cart) {
            const tea = await fetchTeaDetails(cartItem.teaId);
            if (tea) {
                const itemTotal = tea.price * cartItem.quantity;
                total += itemTotal;

                const cartItemElement = document.createElement('div');
                cartItemElement.classList.add('cart-item');
                cartItemElement.innerHTML = `
                    <img src="https://via.placeholder.com/50" alt="${tea.name}">
                    <h4>${tea.name}</h4>
                    <p>Price: $${tea.price}</p>
                    <input type="number" class="item-quantity" data-tea-id="${tea.id}" value="${cartItem.quantity}" min="1">
                    <button class="remove-item-btn" data-tea-id="${tea.id}">Remove</button>
                    <p>Subtotal: $${itemTotal.toFixed(2)}</p>
                `;
                cartItemsContainer.appendChild(cartItemElement);
            }
        }

        cartTotalSpan.textContent = total.toFixed(2);

        document.querySelectorAll('.item-quantity').forEach(input => {
            input.addEventListener('change', async (event) => {
                const teaId = parseInt(event.target.getAttribute('data-tea-id'));
                const newQuantity = parseInt(event.target.value);
                await updateQuantity(teaId, newQuantity);
            });
        });

        document.querySelectorAll('.remove-item-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const teaId = parseInt(event.target.getAttribute('data-tea-id'));
                await removeItem(teaId);
            });
        });
    }

    async function renderCheckoutPage() {
        if (!checkoutCartItems) return; // Only run on checkout page

        checkoutCartItems.innerHTML = '';
        let subtotal = 0;

        if (cart.length === 0) {
            checkoutCartItems.innerHTML = '<p>Your cart is empty. Please add items to your cart before checking out.</p>';
            checkoutSubtotalSpan.textContent = '0.00';
            finalOrderTotalSpan.textContent = '0.00';
            if (placeOrderBtn) placeOrderBtn.disabled = true;
            return;
        }

        for (const cartItem of cart) {
            const tea = await fetchTeaDetails(cartItem.teaId);
            if (tea) {
                const itemTotal = tea.price * cartItem.quantity;
                subtotal += itemTotal;

                const checkoutItemElement = document.createElement('div');
                checkoutItemElement.classList.add('checkout-item');
                checkoutItemElement.innerHTML = `
                    <p>${tea.name} x ${cartItem.quantity} - $${itemTotal.toFixed(2)}</p>
                `;
                checkoutCartItems.appendChild(checkoutItemElement);
            }
        }

        checkoutSubtotalSpan.textContent = subtotal.toFixed(2);
        updateFinalTotal(subtotal);

        if (deliveryOptions) {
            deliveryOptions.addEventListener('change', (event) => {
                if (event.target.name === 'delivery-type') {
                    const selectedType = event.target.value;
                    if (selectedType === 'pickup') {
                        pickupLocationDiv.style.display = 'block';
                        deliveryAddressDiv.style.display = 'none';
                        deliveryFeeSpan.textContent = '0.00';
                    } else {
                        pickupLocationDiv.style.display = 'none';
                        deliveryAddressDiv.style.display = 'block';
                        deliveryFeeSpan.textContent = DELIVERY_FEE.toFixed(2);
                    }
                    updateFinalTotal(subtotal);
                }
            });
        }

        if (placeOrderBtn) {
            placeOrderBtn.addEventListener('click', () => {
                alert('Order Placed! (Not really, this is a placeholder)');
                // Here you would send the order data to your backend
                // For now, clear the cart and redirect
                cart = [];
                saveCart();
                window.location.href = 'home.html';
            });
        }
    }

    function updateFinalTotal(subtotal) {
        let currentDeliveryFee = 0;
        const deliveryTypeRadios = document.querySelectorAll('input[name="delivery-type"]');
        deliveryTypeRadios.forEach(radio => {
            if (radio.checked && radio.value === 'delivery') {
                currentDeliveryFee = DELIVERY_FEE;
            }
        });
        deliveryFeeSpan.textContent = currentDeliveryFee.toFixed(2);
        finalOrderTotalSpan.textContent = (subtotal + currentDeliveryFee).toFixed(2);
    }


    // Fetch and display teas on generic page
    if (teaGallerySection) {
        fetchTeas();
    }

    // Initialize cart counter on all pages
    updateCartCounter();

    // Render page-specific content
    if (window.location.pathname.includes('cart.html')) {
        renderCartPage();
    } else if (window.location.pathname.includes('checkout.html')) {
        renderCheckoutPage();
    }
});