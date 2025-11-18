# Architecture - Cart Feedback System

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (generic.html)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  JavaScript Layer (main.js)                            │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  ┌─ displayNotification()                               │    │
│  │  │  Creates toast message (top-right)                  │    │
│  │  │  ├─ Success: Green (#4CAF50)                        │    │
│  │  │  └─ Error: Red (#f44336)                           │    │
│  │  │                                                     │    │
│  │  ├─ updateStockDisplay()                              │    │
│  │  │  ├─ Finds tea card element                         │    │
│  │  │  ├─ Updates "Stock: X" text                        │    │
│  │  │  └─ Orange flash animation                         │    │
│  │  │                                                     │    │
│  │  ├─ addToCartWithNotification()                       │    │
│  │  │  ├─ Check if user logged in                        │    │
│  │  │  ├─ [If logged in]                                 │    │
│  │  │  │  ├─ POST /api/cart/add/                         │    │
│  │  │  │  ├─ GET /api/teas/{id}/ (get new stock)         │    │
│  │  │  │  └─ syncLocalCartWithBackend()                  │    │
│  │  │  ├─ [If not logged in]                             │    │
│  │  │  │  ├─ Add to localStorage                         │    │
│  │  │  │  └─ Reduce stock locally                        │    │
│  │  │  ├─ updateStockDisplay()                           │    │
│  │  │  ├─ displayNotification()                          │    │
│  │  │  └─ updateCartCounter()                            │    │
│  │  │                                                     │    │
│  │  └─ syncLocalCartWithBackend()                        │    │
│  │     Converts: { items: [{tea: {...}, qty: 1}, ...] }  │    │
│  │     Into: [{ teaId: 1, quantity: 1 }, ...]            │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  CSS Layer (style.css)                                 │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  @keyframes slideIn                                    │    │
│  │  ├─ 0%:   translateX(400px), opacity: 0               │    │
│  │  └─ 100%: translateX(0), opacity: 1                   │    │
│  │  Duration: 0.3s ease-in                               │    │
│  │                                                         │    │
│  │  @keyframes slideOut                                   │    │
│  │  ├─ 0%:   translateX(0), opacity: 1                   │    │
│  │  └─ 100%: translateX(400px), opacity: 0               │    │
│  │  Duration: 0.3s ease-out                              │    │
│  │                                                         │    │
│  │  .notification-success: #4CAF50                        │    │
│  │  .notification-error: #f44336                         │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                               ↓
        ┌──────────────────────┴──────────────────────┐
        ↓                                             ↓
┌──────────────────┐                        ┌────────────────────┐
│  BACKEND (DRF)   │                        │  localStorage      │
├──────────────────┤                        ├────────────────────┤
│                  │                        │                    │
│  POST /api/      │                        │ cart: [            │
│  cart/add/       │                        │  {                 │
│                  │                        │   teaId: 1,        │
│  ├─ Verify tea   │                        │   quantity: 1,     │
│  │   exists      │                        │   cartItemId: X    │
│  │               │                        │  },                │
│  ├─ Check stock  │                        │  ...               │
│  │               │                        │ ]                  │
│  ├─ Deduct stock │                        │                    │
│  │   (atomic)    │                        │ user: {...}        │
│  │               │                        │ token: "..."       │
│  ├─ Create       │                        │                    │
│  │   CartItem    │                        └────────────────────┘
│  │               │
│  └─ Return       │
│     updated      │
│     cart         │
│                  │
│  GET /api/       │
│  teas/{id}/      │
│                  │
│  └─ Return       │
│     updated      │
│     stock        │
│                  │
└──────────────────┘
     ↑
     └─ Authorization: Token {token}
        (only if user logged in)
```

## Event Flow Diagram

```
User clicks "Add to Cart" button
        ↓
┌───────────────────────────────┐
│ button click event handler    │
│ ├─ event.preventDefault()     │
│ ├─ Get teaId from data attr  │
│ ├─ Get teaName from data attr│
│ ├─ Disable button             │
│ └─ Set text to "Adding..."    │
└─────────┬─────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────┐
│ addToCartWithNotification(teaId, teaName, 1)           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────┐                           │
│  │ Is user logged in?      │                           │
│  │ (token in localStorage) │                           │
│  └────────┬────────────────┘                           │
│           │                                            │
│      ┌────┴─────┐                                      │
│      ↓          ↓                                      │
│  YES        NO                                         │
│  ↓          ↓                                          │
│┌──────────┐ ┌──────────┐                              │
││ BACKEND  │ │LOCAL     │                              │
││  PATH    │ │FALLBACK  │                              │
│└─────┬────┘ └────┬─────┘                              │
│      ↓           ↓                                      │
│   [1]         [2]                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
      ↓                           ↓
    [1]                          [2]
┌─────────────────────┐  ┌──────────────────────┐
│  BACKEND PATH:      │  │  LOCAL FALLBACK:     │
├─────────────────────┤  ├──────────────────────┤
│                     │  │                      │
│ POST /api/cart/add/ │  │ const teaInCart =    │
│                     │  │   cart.find(...)     │
│ ├─ tea_id: 1        │  │                      │
│ └─ quantity: 1      │  │ if (teaInCart)       │
│        ↓            │  │   ++quantity         │
│  Backend deducts    │  │ else                 │
│  stock + returns    │  │   add to cart        │
│  updated cart       │  │        ↓             │
│        ↓            │  │ saveCart()           │
│  syncLocal...()     │  │        ↓             │
│  ├─ Convert cart    │  │ teaData[id]          │
│  │   format         │  │   .quantity_in_     │
│  └─ Update local    │  │   stock -= 1         │
│        ↓            │  │        ↓             │
│  GET /api/teas/{id}│  │ updateStockDisplay() │
│        ↓            │  │        ↓             │
│  Get updated stock  │  │ displayNotification()│
│        ↓            │  │        ↓             │
│  updateStockDisplay()│  │ updateCartCounter() │
│        ↓            │  │                      │
│  displayNotification()  │                    │
│        ↓            │                         │
│  updateCartCounter()│                        │
│                     │  │                      │
└────────┬────────────┘  └──────┬───────────────┘
         │                      │
         └──────────┬───────────┘
                    ↓
        ┌───────────────────────────────┐
        │ updateStockDisplay()           │
        │ ├─ Find card element           │
        │ ├─ Update: Stock: 9 (was 10)   │
        │ ├─ Orange color: #ff9800       │
        │ ├─ Fade back to gray: #999     │
        │ └─ Duration: 500ms             │
        └────────────┬────────────────────┘
                     ↓
        ┌───────────────────────────────┐
        │ displayNotification()          │
        │ ├─ Create div element          │
        │ ├─ Position: top-right         │
        │ ├─ Text: "✓ Added 1 × Green   │
        │ │  Tea Blend to cart"          │
        │ ├─ Background: Green           │
        │ ├─ Animation: slideIn (0.3s)   │
        │ ├─ Wait: 3 seconds             │
        │ ├─ Animation: slideOut (0.3s)  │
        │ └─ Remove from DOM             │
        └────────────┬────────────────────┘
                     ↓
        ┌───────────────────────────────┐
        │ updateCartCounter()            │
        │ ├─ Calc: sum of quantities     │
        │ └─ Set counter text            │
        └────────────┬────────────────────┘
                     ↓
        ┌───────────────────────────────┐
        │ Re-enable button               │
        │ ├─ Set disabled = false        │
        │ └─ Set text = "Add to Cart"    │
        └───────────────────────────────┘
```

## Data Structure Flow

### Frontend - teaData Object
```javascript
teaData = {
    1: {
        id: 1,
        name: "Green Tea Blend",
        price: 12.99,
        description: "...",
        quantity_in_stock: 9,  // ← Updated after add-to-cart
        category: {...},
        ...other fields
    },
    2: {
        id: 2,
        name: "Black Tea",
        price: 14.99,
        quantity_in_stock: 3,
        ...
    }
}
```

### Backend - Cart Response
```json
{
    "id": 5,
    "user": 1,
    "items": [
        {
            "id": 12,
            "tea": {
                "id": 1,
                "name": "Green Tea Blend",
                "price": "12.99",
                "quantity_in_stock": 9
            },
            "quantity": 1,
            "cart": 5
        }
    ],
    "total": 12.99
}
```

### Frontend - localStorage Cart
```javascript
cart = [
    {
        teaId: 1,
        quantity: 1,
        cartItemId: 12  // ← From backend if logged in
    },
    {
        teaId: 2,
        quantity: 2,
        cartItemId: 13
    }
]
```

## State Machine - Button States

```
┌──────────────┐
│  Initial     │
│ "Add to Cart"│
│ enabled      │
└──────┬───────┘
       │ User clicks
       ↓
┌──────────────────┐
│ "Adding..."      │
│ disabled         │  ← 0-500ms (async operation)
└─────┬────────────┘
      │ Operation completes
      ↓
┌──────────────────────┐
│ "Add to Cart"        │
│ enabled              │
└──────────────────────┘
      ↑                 │
      └─────────────────┘
        User can click again
```

## Timing Diagram

```
Time    0ms   100ms   200ms   300ms   400ms   500ms   1000ms  3000ms  3300ms
        │      │       │       │       │       │       │       │       │
User    ┤ click
        ┤
API     ┤ ───────────────────────────────────────────────────────────
Call    ┤                    response (200-500ms depending on server)
        ┤
Stock   ┤                              update + animation
Update  ┤                              ├─ orange: 0-500ms
        ┤                              └─ return: 500ms
        ┤
Notif.  ┤                                    slide-in
        ┤                                    ├─ 0-300ms fade-in
Display ┤                                    │
        ┤                                    ├─ 300-3000ms display
        ┤                                    │
        ┤                                    └─ 3000-3300ms fade-out
        ┤                                       remove from DOM
        │      │       │       │       │       │       │       │       │
```

## State Variables Involved

```
[On Click]
  ↓
event.target.disabled = true          // Button state
event.target.textContent = "Adding..."  // Button text
  ↓
[During API Call]
  ↓
token (from localStorage)              // Auth check
teaData[teaId].quantity_in_stock      // Original stock
  ↓
[On Success]
  ↓
cart[].push/update                     // Update cart
teaData[teaId].quantity_in_stock = X   // Update teaData
updateStockDisplay()                   // Update DOM
  ↓
[Notification Shows]
  ↓
notification.style.animation           // slideIn animation
notification.textContent               // Success message
cartCounter.textContent                // Update counter
  ↓
[After 3 seconds]
  ↓
notification.style.animation           // slideOut animation
notification.remove()                  // Remove from DOM
  ↓
event.target.disabled = false           // Re-enable button
event.target.textContent = "Add to Cart" // Restore text
```

## Error Handling Flow

```
[Try to add to cart]
      ↓
  ┌───────────────────┐
  │ Network error?    │
  └────┬──────┬───────┘
       │      │
      YES    NO
       │      │
       ↓      └──────┐
   catch()           ↓
       ↓        Response.ok?
   ┌────────────────┐
   │"Error adding   │       NO
   │to cart"        │        ↓
   │(red notif)     │    ┌──────────────────────┐
   └────────────────┘    │ await response.json()│
                         └────┬─────────────────┘
                              ↓
                         error.error
                              ↓
                         "Error: {message}"
                         (red notification)
```

This architecture ensures smooth, responsive feedback to users while maintaining data consistency between frontend and backend.
