# Frontend Authentication UI - Visual Guide

## Before Login

### What the user sees:
```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    myBru                                        │
│       with a touch of couture!                                  │
│                                                                 │
│  Master the Art of Intentional Brewing...                       │
│                                                                 │
│                                    [🛒 Cart] [Login] [Sign Up] │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### HTML Structure:
```html
<div class="auth-section">
    <div id="auth-links" class="auth-links">
        <a href="login.html" class="btn-login">Login</a>
        <a href="signup.html" class="btn-signup">Sign Up</a>
    </div>
</div>
```

---

## After Login

### What the user sees:
```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    myBru                                        │
│       with a touch of couture!                                  │
│                                                                 │
│  Master the Art of Intentional Brewing...                       │
│                                                                 │
│                        [🛒 Cart] [john_doe] [Logout]           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### HTML Structure:
```html
<div class="auth-section">
    <div id="user-menu" class="user-menu">
        <span id="user-name" class="user-name">john_doe</span>
        <button id="logout-btn" class="btn-logout">Logout</button>
    </div>
</div>
```

---

## Full Header Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐│
│  │ myBru                       │  │ [🛒 Cart]                  ││
│  │ with a touch of couture!    │  │ [username] [Logout]        ││
│  │                             │  │                            ││
│  │ Master the Art of...        │  │ OR                         ││
│  │                             │  │ [Login] [Sign Up]          ││
│  └─────────────────────────────┘  └─────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### Header Structure:
```html
<header>
    <div class="header-top">
        <div><!-- Content on left -->
            <h1>myBru...</h1>
            <p>Master the Art...</p>
        </div>
        <div class="header-right"><!-- Content on right -->
            <div class="cart-container">
                <a href="cart.html" id="cart-icon">
                    🛒 <span id="cart-counter">0</span>
                </a>
            </div>
            <div class="auth-section">
                <!-- User menu OR Login/Sign Up -->
            </div>
        </div>
    </div>
</header>
```

---

## Login/Sign Up Buttons

### Not Logged In (HTML):
```html
<div id="auth-links" class="auth-links" style="display: flex;">
    <a href="login.html" class="btn-login">Login</a>
    <a href="signup.html" class="btn-signup">Sign Up</a>
</div>
```

### Styling (CSS):
```css
.btn-login {
    color: #EAEAEA;
    border: 1px solid #8B4513;
    background-color: transparent;
    padding: 8px 15px;
    border-radius: 4px;
}

.btn-login:hover {
    background-color: #8B4513;
}

.btn-signup {
    background-color: #8B4513;
    color: white;
    padding: 8px 15px;
    border-radius: 4px;
}

.btn-signup:hover {
    background-color: #6B3410;
}
```

---

## User Menu Display

### Logged In (HTML):
```html
<div id="user-menu" class="user-menu" style="display: flex;">
    <span id="user-name" class="user-name">john_doe</span>
    <button id="logout-btn" class="btn-logout">Logout</button>
</div>
```

### Styling (CSS):
```css
.user-menu {
    display: flex;
    align-items: center;
    gap: 10px;
    background-color: rgba(139, 69, 19, 0.1);
    padding: 8px 12px;
    border-radius: 5px;
    border: 1px solid #8B4513;
}

.user-name {
    color: #FFD700;  /* Golden color */
    font-weight: bold;
    font-size: 0.95rem;
}

.btn-logout {
    background-color: #8B4513;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 3px;
    cursor: pointer;
    font-weight: bold;
}

.btn-logout:hover {
    background-color: #6B3410;
}
```

---

## JavaScript Logic

### Check Authentication Status:
```javascript
function checkAuthStatus() {
    const user = JSON.parse(localStorage.getItem('user'));
    const token = localStorage.getItem('token');

    if (user && token) {
        // User is logged in
        authLinks.style.display = 'none';      // Hide login/signup
        userMenu.style.display = 'flex';       // Show user menu
        userNameSpan.textContent = user.username || user.email;
    } else {
        // User is not logged in
        authLinks.style.display = 'flex';      // Show login/signup
        userMenu.style.display = 'none';       // Hide user menu
    }
}
```

### Handle Logout:
```javascript
function logout() {
    const token = localStorage.getItem('token');
    
    // Call backend logout
    fetch(`${API_URL}/auth/logout/`, {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        // Clear localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Update UI
        checkAuthStatus();
        
        // Redirect to home
        window.location.href = 'home.html';
    })
    .catch(error => {
        // Even if backend fails, clear data and redirect
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        checkAuthStatus();
        window.location.href = 'home.html';
    });
}
```

---

## How It Works on Each Page

### Page Load Sequence:
1. HTML loads with both `user-menu` and `auth-links` elements
2. JavaScript runs `checkAuthStatus()` on DOMContentLoaded
3. Checks localStorage for token and user
4. Shows appropriate UI (login buttons OR user menu)
5. Sets up logout button click handler

### Navigation Between Pages:
1. User clicks link to another page
2. New page loads with same header structure
3. JavaScript runs again on page load
4. Checks localStorage (same data still there)
5. Shows same auth status on new page

### After Login:
1. User submits login form on login.html
2. Frontend gets token and user from backend
3. Stores both in localStorage
4. Redirects to home.html (or another page)
5. New page checks localStorage
6. Shows user menu instead of login buttons

### After Logout:
1. User clicks Logout button
2. Backend invalidates token
3. Frontend clears localStorage
4. Page reloads or redirects
5. checkAuthStatus() runs
6. Shows login buttons again

---

## Updates Across All Pages

The following pages now have the new authentication UI:

✅ **home.html**
- New header layout with auth section
- User menu displays username
- Logout button available

✅ **generic.html**
- New header layout with cart and auth
- Shows cart counter
- User menu displays

✅ **cart.html**
- New header with cart link
- User menu displays
- Cart counter updates

✅ **checkout.html**
- New header with cart link
- User menu displays
- Login status visible

✅ **login.html** (Already has auth UI)
- Has Google OAuth button
- Traditional login form

✅ **signup.html** (Already has auth UI)
- Has Google OAuth button
- Registration form

---

## Color Scheme

- **Primary Brown**: #8B4513 (buttons, borders)
- **Dark Brown Hover**: #6B3410 (button hover state)
- **Username Color**: #FFD700 (Golden)
- **Text**: #EAEAEA (Light gray)
- **Background**: #36454F (Charcoal)
- **Menu Background**: rgba(139, 69, 19, 0.1) (Semi-transparent brown)

---

## Responsive Behavior

The header uses flexbox and responds to screen size:

### Desktop (Wide Screen):
```
[Logo/Title] ........... [Cart] [Username] [Logout]
```

### Mobile (Narrow Screen):
- Flex wraps as needed
- Auth section still visible
- Cart counter still shows
- All buttons remain accessible

---

## What User Data is Displayed

From localStorage, the following is shown:
- **Username**: User's username (displayed in golden color)
- Falls back to email if username is not set

Example:
```javascript
// After login, localStorage contains:
{
    "token": "abc123def456...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}

// UI displays: "john_doe" (or "john@example.com" if username is empty)
```

---

## Testing Checklist

- [ ] Page loads, shows Login/Sign Up if not logged in
- [ ] Click Login, enter credentials
- [ ] Redirected to home, username appears
- [ ] Navigate to other pages, username persists
- [ ] Click Logout button
- [ ] Redirected to home, Login/Sign Up reappear
- [ ] Open DevTools, check localStorage cleared
- [ ] Test on different pages
- [ ] Test on mobile viewport
- [ ] Test Google OAuth (logs in correctly)

---

**Implementation Status: ✅ COMPLETE**

All pages now show:
- User login status
- Logout button when logged in
- Login/Sign Up links when not logged in
- Professional styling consistent with site design
