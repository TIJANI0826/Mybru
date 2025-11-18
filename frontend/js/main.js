// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Inject shared nav partial so header nav is maintained in one place
    try {
        const resp = await fetch('./_nav.html');
        if (resp.ok) {
            const navHtml = await resp.text();
            const siteNav = document.querySelector('.site-nav');
            if (siteNav) {
                siteNav.innerHTML = navHtml;
                // mark active link based on current pathname
                const links = siteNav.querySelectorAll('.nav-menu a');
                const path = window.location.pathname.split('/').pop() || 'home.html';
                links.forEach(a => {
                    // remove existing active
                    a.classList.remove('nav-active');
                    const href = a.getAttribute('href');
                    if (href && href.endsWith(path)) {
                        a.classList.add('nav-active');
                    }
                });
            }
        }
    } catch (err) {
        console.error('Failed to load shared nav:', err);
    }

    // Store tea data for reference
    let teaData = {};
    // Local stock overrides persisted for guest flows
    function getLocalTeaStockMap() {
        try {
            return JSON.parse(localStorage.getItem('teaStock') || '{}');
        } catch (e) {
            return {};
        }
    }

    function setLocalTeaStock(teaId, stock) {
        const map = getLocalTeaStockMap();
        map[teaId] = stock;
        localStorage.setItem('teaStock', JSON.stringify(map));
    }

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
        const token = localStorage.getItem('token');
        if (!token) {
            // Not logged in, don't update counter
            if (cartCounter) cartCounter.textContent = '0';
            return;
        }
        
        // Fetch cart from backend if logged in
        fetch(`${API_URL}/cart/`, { headers: getAuthHeaders() })
            .then(r => {
                if (r.ok) return r.json();
                throw new Error('Failed to fetch cart');
            })
            .then(data => {
                if (cartCounter && data.items) {
                    const qty = data.items.reduce((acc, it) => acc + (it.quantity || 0), 0);
                    cartCounter.textContent = qty;
                }
            })
            .catch(err => {
                console.error('Could not update cart counter:', err);
                if (cartCounter) cartCounter.textContent = '0';
            });
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

        const token = localStorage.getItem('token');

        // Require backend sync for all operations
        if (!token || !cartItem.cartItemId) {
            displayNotification('Authentication required for cart updates', 'error');
            return;
        }

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

                // Refresh tea info to get updated stock from backend
                try {
                    const teaResp = await fetch(`${API_URL}/teas/${teaId}/`, { headers: getAuthHeaders() });
                    if (teaResp.ok) {
                        const updatedTea = await teaResp.json();
                        teaData[teaId] = updatedTea;
                        updateStockDisplay(teaId, updatedTea.quantity_in_stock);
                        displayNotification(`✓ Quantity updated`, 'success');
                    }
                } catch (err) {
                    console.error('Failed to refresh tea after update:', err);
                }

                if (window.location.pathname.includes('cart.html')) {
                    renderCartPage();
                }
            } else {
                const err = await response.json();
                displayNotification(`Error: ${err.error || 'Could not update cart'}`, 'error');
            }
        } catch (error) {
            console.error('Error updating cart item:', error);
            displayNotification('Error updating cart', 'error');
        }
    }

    async function removeItem(teaId) {
        const cartItem = cart.find(item => item.teaId === teaId);
        if (!cartItem) return;

        const token = localStorage.getItem('token');

        // Require backend sync for all operations
        if (!token || !cartItem.cartItemId) {
            displayNotification('Authentication required for cart updates', 'error');
            return;
        }

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
                        displayNotification(`✓ Item removed from cart`, 'success');
                    }
                } catch (err) {
                    console.error('Failed to refresh tea after remove:', err);
                }

                if (window.location.pathname.includes('cart.html')) {
                    renderCartPage();
                }
            } else {
                const err = await response.json();
                displayNotification(`Error: ${err.error || 'Could not remove from cart'}`, 'error');
            }
        } catch (error) {
            console.error('Error removing cart item:', error);
            displayNotification('Error removing item from cart', 'error');
        }
    }

    const API_URL = 'http://localhost:8000/api';
    const BACKEND_BASE = API_URL.replace(/\/api\/?$/, '');

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
        
        // Always require authenticated backend sync
        if (!token) {
            displayNotification('Please log in to add items to cart', 'error');
            window.location.href = 'login.html';
            return;
        }
        
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
                
                // Get updated tea data from backend
                const teaResponse = await fetch(`${API_URL}/teas/${teaId}/`, {
                    headers: getAuthHeaders()
                });
                
                if (teaResponse.ok) {
                    const updatedTea = await teaResponse.json();
                    teaData[teaId] = updatedTea;
                    
                    // Update stock display with backend truth
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
        const localStock = getLocalTeaStockMap();

        teas.forEach((tea, i) => {
            const teaCard = document.createElement('div');
            teaCard.classList.add('tea-card', 'slide-down');
            teaCard.setAttribute('data-tea-id', tea.id);
            teaCard.tabIndex = 0; // make focusable
            teaCard.setAttribute('role', 'button');
            teaCard.setAttribute('aria-label', `${tea.name} - view details`);
            // Stagger appearance for a nicer effect
            teaCard.style.animationDelay = `${i * 80}ms`;

            // prefer persisted local stock overrides for guest flows
            const displayedStock = (localStock && localStock[tea.id] !== undefined) ? localStock[tea.id] : tea.quantity_in_stock;
            // ensure tea object reflects the displayed stock
            tea.quantity_in_stock = displayedStock;

            teaCard.innerHTML = `
                <div class="tea-card-image">
                    <img src="${(tea.image ? (tea.image.startsWith('http') ? tea.image : BACKEND_BASE + tea.image) : 'https://via.placeholder.com/200x200')}" alt="${tea.name}">
                </div>
                <div class="tea-card-content">
                    <h4>${tea.name}</h4>
                    <p>${tea.description}</p>
                    <div class="tea-card-footer">
                        <div class="tea-card-price">$${tea.price}</div>
                        <div class="tea-card-stock" data-stock="${displayedStock}">Stock: ${displayedStock}</div>
                    </div>
                    <button class="add-to-cart-btn" data-tea-id="${tea.id}" data-tea-name="${tea.name}">Add to Cart</button>
                </div>
            `;

            teaGalleryContainer.appendChild(teaCard);

            // Store tea data globally for later reference
            teaData[tea.id] = tea;

            // Open product detail when the card (but not its inner button) is clicked
            teaCard.addEventListener('click', (e) => {
                if (e.target.closest('.add-to-cart-btn')) return; // let button handle it
                window.location.href = `product.html?id=${tea.id}`;
            });

            // Keyboard accessibility: Enter or Space opens detail
            teaCard.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    teaCard.click();
                }
            });
        });

        // Hook add-to-cart buttons (delegated within gallery) -- still works after cards
        teaGalleryContainer.querySelectorAll('.add-to-cart-btn').forEach(button => {
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

        const token = localStorage.getItem('token');
        if (!token) {
            cartItemsContainer.innerHTML = '<p>Please <a href="login.html">log in</a> to view your cart.</p>';
            cartTotalSpan.textContent = '0.00';
            return;
        }

        try {
            // Fetch cart from backend API
            const response = await fetch(`${API_URL}/cart/`, {
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch cart');
            }

            const backendCart = await response.json();
            
            // Sync local cart with backend
            syncLocalCartWithBackend(backendCart);

            cartItemsContainer.innerHTML = '';
            let total = 0;

            if (!backendCart.items || backendCart.items.length === 0) {
                cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
                cartTotalSpan.textContent = '0.00';
                return;
            }

            for (const cartItem of backendCart.items) {
                const tea = cartItem.tea;
                if (tea) {
                    const itemTotal = tea.price * cartItem.quantity;
                    total += itemTotal;

                    const cartItemElement = document.createElement('div');
                    cartItemElement.classList.add('cart-item');
                    cartItemElement.innerHTML = `
                        <img src="${(tea.image ? (tea.image.startsWith('http') ? tea.image : BACKEND_BASE + tea.image) : 'https://via.placeholder.com/50')}" alt="${tea.name}">
                        <h4>${tea.name}</h4>
                        <p>Price: $${tea.price}</p>
                        <input type="number" class="item-quantity" data-tea-id="${tea.id}" data-cart-item-id="${cartItem.id}" value="${cartItem.quantity}" min="1">
                        <button class="remove-item-btn" data-tea-id="${tea.id}" data-cart-item-id="${cartItem.id}">Remove</button>
                        <p>Subtotal: $${itemTotal.toFixed(2)}</p>
                    `;
                    cartItemsContainer.appendChild(cartItemElement);
                    
                    // Store tea data for reference
                    teaData[tea.id] = tea;
                }
            }

            cartTotalSpan.textContent = total.toFixed(2);

            // Setup quantity change handlers
            document.querySelectorAll('.item-quantity').forEach(input => {
                input.addEventListener('change', async (event) => {
                    const teaId = parseInt(event.target.getAttribute('data-tea-id'));
                    const cartItemId = parseInt(event.target.getAttribute('data-cart-item-id'));
                    const newQuantity = parseInt(event.target.value);
                    
                    // Find and update cart item locally
                    const cartItem = cart.find(item => item.teaId === teaId);
                    if (cartItem) {
                        cartItem.cartItemId = cartItemId;
                    }
                    
                    await updateQuantity(teaId, newQuantity);
                });
            });

            // Setup remove handlers
            document.querySelectorAll('.remove-item-btn').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const teaId = parseInt(event.target.getAttribute('data-tea-id'));
                    const cartItemId = parseInt(event.target.getAttribute('data-cart-item-id'));
                    
                    // Find and update cart item locally
                    const cartItem = cart.find(item => item.teaId === teaId);
                    if (cartItem) {
                        cartItem.cartItemId = cartItemId;
                    }
                    
                    await removeItem(teaId);
                });
            });

        } catch (error) {
            console.error('Error rendering cart page:', error);
            cartItemsContainer.innerHTML = '<p>Error loading cart. Please refresh the page.</p>';
            cartTotalSpan.textContent = '0.00';
        }
    }

    async function renderCheckoutPage() {
        if (!checkoutCartItems) return; // Only run on checkout page
        // Require authentication for checkout flows
        const token = localStorage.getItem('token');
        if (!token) {
            checkoutCartItems.innerHTML = '<p>Please <a href="login.html">log in</a> to checkout.</p>';
            checkoutSubtotalSpan.textContent = '0.00';
            finalOrderTotalSpan.textContent = '0.00';
            if (placeOrderBtn) placeOrderBtn.disabled = true;
            return;
        }

        // Fetch authoritative cart from backend
        let backendCart;
        try {
            const resp = await fetch(`${API_URL}/cart/`, { headers: getAuthHeaders() });
            if (!resp.ok) throw new Error('Failed to fetch cart');
            backendCart = await resp.json();
            syncLocalCartWithBackend(backendCart);
        } catch (err) {
            console.error('Failed to load cart for checkout:', err);
            checkoutCartItems.innerHTML = '<p>Could not load cart. Try again later.</p>';
            return;
        }

        checkoutCartItems.innerHTML = '';
        let subtotal = 0;

        if (!backendCart.items || backendCart.items.length === 0) {
            checkoutCartItems.innerHTML = '<p>Your cart is empty. Please add items to your cart before checking out.</p>';
            checkoutSubtotalSpan.textContent = '0.00';
            finalOrderTotalSpan.textContent = '0.00';
            if (placeOrderBtn) placeOrderBtn.disabled = true;
            return;
        }

        for (const cartItem of backendCart.items) {
            const tea = cartItem.tea;
            if (tea) {
                const itemTotal = tea.price * cartItem.quantity;
                subtotal += itemTotal;

                const checkoutItemElement = document.createElement('div');
                checkoutItemElement.classList.add('checkout-item');
                checkoutItemElement.innerHTML = `
                    <p>${tea.name} x ${cartItem.quantity} - $${itemTotal.toFixed(2)}</p>
                `;
                checkoutCartItems.appendChild(checkoutItemElement);

                // store tea for potential later reference
                teaData[tea.id] = tea;
            }
        }

        checkoutSubtotalSpan.textContent = subtotal.toFixed(2);
        updateFinalTotal(subtotal);

        // Populate pickup locations and user's saved delivery addresses
        try {
            // pickup locations
            const puResp = await fetch(`${API_URL}/pickup-locations/`);
            if (puResp.ok) {
                const pickups = await puResp.json();
                const pickupSelect = document.getElementById('pickup-select');
                if (pickupSelect) {
                    pickupSelect.innerHTML = '';
                    pickups.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = `${p.name} (${p.branch}) — ${p.address}`;
                        pickupSelect.appendChild(opt);
                    });
                    // Ensure the select is enabled and focusable
                    pickupSelect.disabled = false;
                    pickupSelect.tabIndex = 0;
                    pickupSelect.style.pointerEvents = 'auto';
                    pickupSelect.style.zIndex = 10;

                    // If there are pickups, select the first and update delivery fee
                    if (pickups.length > 0) {
                        pickupSelect.value = pickups[0].id;
                        // store delivery fee on the select for quick lookup
                        pickupSelect._pickupMap = {};
                        pickups.forEach(p => pickupSelect._pickupMap[p.id] = p);
                        const p0 = pickups[0];
                        deliveryFeeSpan.textContent = (p0.delivery_fee || 0).toFixed(2);
                    }

                    // Update delivery fee when user changes pickup location
                    pickupSelect.addEventListener('change', (e) => {
                        const sel = e.target.value;
                        const map = e.target._pickupMap || {};
                        const picked = map[sel];
                        const fee = picked ? (picked.delivery_fee || 0) : 0;
                        deliveryFeeSpan.textContent = Number(fee).toFixed(2);
                        // Recompute final total (use current subtotal displayed)
                        const subtotal = parseFloat(checkoutSubtotalSpan.textContent) || 0;
                        finalOrderTotalSpan.textContent = (subtotal + Number(fee)).toFixed(2);
                    });
                }
            }

            // user's saved delivery addresses
            const addrResp = await fetch(`${API_URL}/delivery-addresses/`, { headers: getAuthHeaders() });
            if (addrResp.ok) {
                const addrs = await addrResp.json();
                const addrSelect = document.getElementById('delivery-address-select');
                if (addrSelect) {
                    addrSelect.innerHTML = '<option value="">-- Use a new address --</option>';
                    addrs.forEach(a => {
                        const opt = document.createElement('option');
                        opt.value = a.id;
                        opt.textContent = `${a.address_line1}, ${a.city}` + (a.address_line2 ? ` (${a.address_line2})` : '');
                        addrSelect.appendChild(opt);
                    });
                }
            }
        } catch (err) {
            console.error('Failed to load pickup locations or delivery addresses:', err);
        }

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
            placeOrderBtn.addEventListener('click', async () => {
                placeOrderBtn.disabled = true;
                placeOrderBtn.textContent = 'Placing order...';

                const selectedType = document.querySelector('input[name="delivery-type"]:checked').value;
                const payload = { delivery_type: selectedType };

                if (selectedType === 'pickup') {
                    const pickupSelect = document.getElementById('pickup-select');
                    if (!pickupSelect || !pickupSelect.value) {
                        displayNotification('Please select a pickup location', 'error');
                        placeOrderBtn.disabled = false;
                        placeOrderBtn.textContent = 'Place Order';
                        return;
                    }
                    payload.pickup_id = parseInt(pickupSelect.value);
                } else {
                    const addrSelect = document.getElementById('delivery-address-select');
                    const selectedAddrId = addrSelect ? addrSelect.value : '';
                    if (selectedAddrId) {
                        payload.delivery_address_id = parseInt(selectedAddrId);
                    } else {
                        // collect manual fields
                        payload.address_line1 = document.getElementById('address-line1').value;
                        payload.address_line2 = document.getElementById('address-line2').value;
                        payload.city = document.getElementById('city').value;
                        payload.state = document.getElementById('state').value;
                        payload.zip_code = document.getElementById('zip-code').value;
                        payload.delivery_fee = parseFloat(document.getElementById('delivery-fee').textContent) || DELIVERY_FEE;
                        // basic validation
                        if (!payload.address_line1 || !payload.city) {
                            displayNotification('Please provide address line 1 and city for delivery', 'error');
                            placeOrderBtn.disabled = false;
                            placeOrderBtn.textContent = 'Place Order';
                            return;
                        }
                    }
                }

                try {
                    const resp = await fetch(`${API_URL}/checkout/place-order/`, {
                        method: 'POST',
                        headers: getAuthHeaders(),
                        body: JSON.stringify(payload)
                    });

                    if (resp.ok) {
                        const order = await resp.json();
                        displayNotification('Order placed successfully', 'success');
                        // Clear local cart mirror and update counter
                        cart = [];
                        saveCart();
                        // Redirect to order summary or home
                        setTimeout(() => window.location.href = 'home.html', 800);
                        return;
                    } else {
                        const err = await resp.json();
                        displayNotification(`Error: ${err.error || 'Could not place order'}`, 'error');
                    }
                } catch (err) {
                    console.error('Place order failed:', err);
                    displayNotification('Could not place order', 'error');
                }

                placeOrderBtn.disabled = false;
                placeOrderBtn.textContent = 'Place Order';
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
    } else if (window.location.pathname.includes('orders.html')) {
        renderOrdersPage();
    }

    async function renderOrdersPage() {
        const ordersContainer = document.getElementById('orders-container');
        if (!ordersContainer) return;

        const token = localStorage.getItem('token');
        if (!token) {
            ordersContainer.innerHTML = '<p>Please <a href="login.html">log in</a> to view your orders.</p>';
            return;
        }

        ordersContainer.innerHTML = '<p>Loading orders...</p>';
        try {
            const resp = await fetch(`${API_URL}/orders/`, { headers: getAuthHeaders() });
            if (!resp.ok) throw new Error('Failed to fetch orders');
            const orders = await resp.json();

            if (!orders || orders.length === 0) {
                ordersContainer.innerHTML = '<p>No orders found.</p>';
                return;
            }

            ordersContainer.innerHTML = '';
            orders.forEach(order => {
                const el = document.createElement('div');
                el.className = 'order-card';
                const date = new Date(order.created_at).toLocaleString();
                const status = order.ordered ? 'Completed' : 'Pending';
                const delivery = order.delivery_type || 'pickup';
                const address = delivery === 'pickup' ? (order.pickup_location || '') : (order.delivery_address_line1 || '');

                let itemsHtml = '';
                if (order.items && order.items.length) {
                    order.items.forEach(it => {
                        const teaName = it.tea ? it.tea.name : (`Tea #${it.tea}`);
                        itemsHtml += `<div class="order-item"><strong>${teaName}</strong> x ${it.quantity} — $${(it.tea ? it.tea.price : 0)}</div>`;
                    });
                }

                el.innerHTML = `
                    <div class="order-header">
                        <div>Order #${order.id} — <span class="order-status">${status}</span></div>
                        <div>${date}</div>
                    </div>
                    <div>Type: ${delivery}</div>
                    <div>Address/Pickup: ${address}</div>
                    <div>Items:</div>
                    <div class="order-items">${itemsHtml}</div>
                    <div style="margin-top:8px; font-weight:600">Total: $${parseFloat(order.total_price).toFixed(2)}</div>
                `;

                ordersContainer.appendChild(el);
            });
        } catch (err) {
            console.error('Could not load orders:', err);
            ordersContainer.innerHTML = '<p>Error loading orders. Try again later.</p>';
        }
    }
});