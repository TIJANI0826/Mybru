// product.js - render a single product detail and allow adding to cart via backend API
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const API_URL = 'http://localhost:8000/api';
    const BACKEND_BASE = API_URL.replace(/\/api\/?$/, '');
    const container = document.getElementById('product-detail');

    function displayNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `position: fixed; top: 20px; right: 20px; padding: 12px 16px; background-color: ${type === 'success' ? '#4CAF50' : '#f44336'}; color: white; border-radius: 4px; z-index: 10000;`;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 400);
        }, 2600);
    }

    function getAuthHeaders() {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Token ${token}`;
        return headers;
    }

    function updateCartCounter() {
        // Fetch from backend if logged in
        const token = localStorage.getItem('token');
        if (token) {
            fetch(`${API_URL}/cart/`, { headers: getAuthHeaders() })
                .then(r => r.json())
                .then(data => {
                    const cartCounter = document.getElementById('cart-counter');
                    if (cartCounter) {
                        const qty = data.items ? data.items.reduce((acc, it) => acc + (it.quantity || 0), 0) : 0;
                        cartCounter.textContent = qty;
                    }
                })
                .catch(err => console.error('Could not fetch cart:', err));
        }
    }

    if (!id) {
        if (container) container.innerHTML = '<p>Product not specified.</p>';
        return;
    }

    async function fetchAndRender() {
        try {
            const resp = await fetch(`${API_URL}/teas/${id}/`, { headers: getAuthHeaders() });
            if (!resp.ok) throw new Error('Network error');
            const tea = await resp.json();
            renderTea(tea);
        } catch (err) {
            console.error('Failed to load tea:', err);
            if (container) container.innerHTML = '<p>Failed to load product. Try again later.</p>';
        }
    }

    function renderTea(tea) {
        if (!container) return;
        container.innerHTML = `
            <div class="tea-card">
                <div class="tea-card-image">
                    <img src="${(tea.image ? (tea.image.startsWith('http') ? tea.image : BACKEND_BASE + tea.image) : 'https://via.placeholder.com/600x400')}" alt="${tea.name}">
                </div>
                <div class="tea-card-content">
                    <h2>${tea.name}</h2>
                    <p class="tea-card-price">Price: $${tea.price}</p>
                    <p class="tea-card-stock" data-stock="${tea.quantity_in_stock}">In stock: ${tea.quantity_in_stock}</p>
                    <p>${tea.description || ''}</p>
                    <div style="margin-top:12px; display:flex; gap:10px; align-items:center;">
                        <label for="qty">Qty</label>
                        <input id="qty" type="number" min="1" value="1" style="width:80px; padding:6px; border-radius:4px; border:1px solid #ccc;">
                        <button id="add-to-cart" class="add-to-cart-btn">Add to Cart</button>
                    </div>
                </div>
            </div>
        `;

        const addBtn = document.getElementById('add-to-cart');
        const qtyInput = document.getElementById('qty');

        if (addBtn) {
            addBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                const token = localStorage.getItem('token');

                // Require authentication
                if (!token) {
                    displayNotification('Please log in to add items to cart', 'error');
                    window.location.href = 'login.html';
                    return;
                }

                const qty = parseInt(qtyInput.value) || 1;
                addBtn.disabled = true;
                addBtn.textContent = 'Adding...';

                try {
                    // Call backend API to add to cart
                    const response = await fetch(`${API_URL}/cart/add/`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Token ${token}`,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ tea_id: id, quantity: qty })
                    });

                    if (response.ok) {
                        // Fetch updated tea info to show new stock
                        const teaResp = await fetch(`${API_URL}/teas/${id}/`, { headers: getAuthHeaders() });
                        if (teaResp.ok) {
                            const updatedTea = await teaResp.json();
                            const stockEl = document.querySelector('.tea-card-stock');
                            if (stockEl) {
                                stockEl.textContent = `In stock: ${updatedTea.quantity_in_stock}`;
                                stockEl.setAttribute('data-stock', updatedTea.quantity_in_stock);
                            }
                        }
                        displayNotification(`✓ Added ${qty} × ${tea.name} to cart`, 'success');
                        updateCartCounter();
                    } else {
                        const err = await response.json();
                        displayNotification(`Error: ${err.error || 'Could not add to cart'}`, 'error');
                    }
                } catch (err) {
                    console.error('Add to cart failed', err);
                    displayNotification('Could not add to cart', 'error');
                }

                addBtn.disabled = false;
                addBtn.textContent = 'Add to Cart';
            });
        }
    }

    fetchAndRender();
});
