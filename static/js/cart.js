const updateBtns = document.getElementsByClassName('update-cart')

for (let i = 0; i < updateBtns.length; i++) {
    updateBtns[i].addEventListener('click', function () {
        const productId = this.dataset.product
        const action = this.dataset.action
        const countInStock = this.dataset.countInStock
        console.log('productId:', productId, 'Action:', action, 'countInStock:', countInStock)
        console.log('USER:', user)

        if (user === 'AnonymousUser') {
            addCookieItem(productId, action, countInStock)
        } else {
            updateUserOrder(productId, action)
        }
    })
}

function addCookieItem(productId, action, countInStock) {
    let productCountInStock = parseInt(countInStock)

    if (action === 'add') {
        if (cart[productId] === undefined) {
            cart[productId] = {'quantity': 1}
        } else {
            cart[productId]['quantity'] += 1
        }
    }
    if (action === 'addByQty') {
        let qty = parseInt(form.value)

        if (cart[productId] === undefined) {
            cart[productId] = {'quantity': qty}

        } else {
            cart[productId]['quantity'] += qty
        }
    }

    if (cart[productId]['quantity'] >= productCountInStock) {
        cart[productId]['quantity'] = productCountInStock
    }

    if (action === 'remove') {
        cart[productId]['quantity'] -= 1

        if (cart[productId]['quantity'] <= 0) {
            console.log('Item should be deleted')
            delete cart[productId];
        }
    }

    if (action === 'delete') {
        delete cart[productId];
    }

    console.log('CART:', cart)
    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"


    action === 'addByQty' ? window.location.href = "/cart/" : location.reload()
}


function updateUserOrder(productId, action) {
    const url = '/update_item/'

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(
            action === 'addByQty'
            ? {'productId': productId, 'action': action, 'qty': form.value}
            : {'productId': productId, 'action': action}
        )
    })
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            console.log('data:', data);
            action === 'addByQty' ? window.location.href = "/cart/" : location.reload()
        })

}
