document.addEventListener('DOMContentLoaded', () => {
    flight_duration();
});

function flight_duration() {
    document.querySelectorAll(".duration").forEach(element => {
        let time = element.dataset.value.split(":");
        element.innerText = time[0]+"h "+time[1]+"m";
    });
}


function add_traveller() {
    let div = document.querySelector('.add-traveller-div');
    let fname = div.querySelector('#fname');
    let lname = div.querySelector('#lname');
    let gender = div.querySelectorAll('.gender');
    let gender_val = null
    if(fname.value.trim().length === 0) {
        alert("Please enter First Name.");
        return false;
    }

    if(lname.value.trim().length === 0) {
        alert("Please enter Last Name.");
        return false;
    }

    if (!gender[0].checked) {
        if (!gender[1].checked) {
            alert("Please select gender.");
            return false;
        }
        else {
            gender_val = gender[1].value;
        }
    }
    else {
        gender_val = gender[0].value;
    }

    let passengerCount = div.parentElement.querySelectorAll(".each-traveller-div .each-traveller").length;

    let traveller = `<div class="row each-traveller">
                        <div>
                            <span class="traveller-name">${fname.value} ${lname.value}</span><span>,</span>
                            <span class="traveller-gender">${gender_val.toUpperCase()}</span>
                        </div>
                        <input type="hidden" name="passenger${passengerCount+1}FName" value="${fname.value}">
                        <input type="hidden" name="passenger${passengerCount+1}LName" value="${lname.value}">
                        <input type="hidden" name="passenger${passengerCount+1}Gender" value="${gender_val}">
                        <div class="delete-traveller">
                            <button class="btn" type="button" onclick="del_traveller(this)">
                                <svg width="1.1em" height="1.1em" viewBox="0 0 16 16" class="bi bi-x-circle" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                    <path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                    <path fill-rule="evenodd" d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                                </svg>
                            </button>
                        </div>
                    </div>`;
    div.parentElement.querySelector(".each-traveller-div").innerHTML += traveller;
    div.parentElement.querySelector("#p-count").value = passengerCount+1;
    div.parentElement.querySelector(".traveller-head h6 span").innerText = passengerCount+1;
    div.parentElement.querySelector(".no-traveller").style.display = 'none';
    fname.value = "";
    lname.value = "";
    gender.forEach(radio => {
        radio.checked = false;
    });

    let pcount = document.querySelector("#p-count").value;
    let fare = document.querySelector("#basefare").value;
    let fee = document.querySelector("#fee").value;
    if (parseInt(pcount)!==0) {
        document.querySelector(".base-fare-value span").innerText = parseInt(fare)*parseInt(pcount);
        document.querySelector(".total-fare-value span").innerText = (parseInt(fare)*parseInt(pcount))+parseInt(fee);
    }

}

function del_traveller(btn) {
    let traveller = btn.parentElement.parentElement;
    let tvl = btn.parentElement.parentElement.parentElement.parentElement;
    let cnt = tvl.querySelector("#p-count");
    cnt.value = parseInt(cnt.value)-1;
    tvl.querySelector(".traveller-head h6 span").innerText = cnt.value;
    if(parseInt(cnt.value) <= 0) {
        tvl.querySelector('.no-traveller').style.display = 'block';
    }
    traveller.remove();
    
    let pcount = document.querySelector("#p-count").value;
    let fare = document.querySelector("#basefare").value;
    let fee = document.querySelector("#fee").value;
    if (parseInt(pcount) !== 0) {
        document.querySelector(".base-fare-value span").innerText = parseInt(fare)*parseInt(pcount);
        document.querySelector(".total-fare-value span").innerText = (parseInt(fare)*parseInt(pcount))+parseInt(fee);   
    }
}

function book_submit() {
    let pcount = document.querySelector("#p-count");
    let requiredPassengers = document.querySelector("#required-passengers");
    let required = requiredPassengers ? parseInt(requiredPassengers.value) : 1;
    let current = parseInt(pcount.value);
    
    // Check if we have at least one passenger
    if(current <= 0) {
        showPassengerValidationModal(required, current);
        return false;
    }
    
    // Check if passenger count matches required seats
    if(current < required) {
        showPassengerValidationModal(required, current);
        return false;
    }
    
    return true;
}

function showPassengerValidationModal(required, current) {
    // Update modal message
    let missing = required - current;
    let messageEl = document.getElementById('passengerValidationMessage');
    let seatCountEl = document.getElementById('modal-seat-count');
    let passengerCountEl = document.getElementById('modal-passenger-count');
    
    if (messageEl) {
        if (current === 0) {
            messageEl.textContent = `Please add details for ${required} passenger(s) to proceed.`;
        } else {
            messageEl.textContent = `Please add ${missing} more passenger(s) to match your seat selection.`;
        }
    }
    
    if (seatCountEl) seatCountEl.textContent = required;
    if (passengerCountEl) passengerCountEl.textContent = current;
    
    // Show the modal using jQuery (Bootstrap 4)
    $('#passengerValidationModal').modal('show');
}

// ===== Coupon Functionality =====
document.addEventListener('DOMContentLoaded', () => {
    initCouponSystem();
});

function initCouponSystem() {
    const couponInput = document.getElementById('coupon-input');
    const applyBtn = document.getElementById('apply-coupon-btn');
    const removeBtn = document.getElementById('remove-coupon-btn');
    const couponItems = document.querySelectorAll('.coupon-item');
    
    if (!couponInput) return;
    
    // Coupon data (synced with HTML data attributes)
    const coupons = {
        'HDFC10': { discount: 10, type: 'percent', minOrder: 0 },
        'ICICI15': { discount: 15, type: 'percent', minOrder: 0 },
        'SBI500': { discount: 500, type: 'flat', minOrder: 3000 }
    };
    
    // Click on coupon item to select
    couponItems.forEach(item => {
        item.addEventListener('click', () => {
            const code = item.dataset.code;
            couponInput.value = code;
            // Hide dropdown after selection
            document.getElementById('coupon-dropdown').style.visibility = 'hidden';
            setTimeout(() => {
                document.getElementById('coupon-dropdown').style.visibility = '';
            }, 300);
        });
    });
    
    // Apply button click
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            applyCoupon(coupons, couponInput.value.toUpperCase().trim());
        });
    }
    
    // Remove coupon
    if (removeBtn) {
        removeBtn.addEventListener('click', () => {
            removeCoupon();
        });
    }
    
    // Enter key to apply
    couponInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyCoupon(coupons, couponInput.value.toUpperCase().trim());
        }
    });
}

function applyCoupon(coupons, code) {
    const coupon = coupons[code];
    const msgDiv = document.getElementById('coupon-applied-msg');
    const savingsSpan = document.getElementById('savings-amount');
    const discountInput = document.getElementById('coupon-discount-value');
    
    if (!coupon) {
        alert('Invalid coupon code. Please try again.');
        return;
    }
    
    // Get current fare values
    const pcount = parseInt(document.querySelector("#p-count").value) || 1;
    const baseFare = parseInt(document.querySelector("#basefare").value) * pcount;
    const fee = parseInt(document.querySelector("#fee").value);
    const totalFare = baseFare + fee;
    
    // Check minimum order
    if (coupon.minOrder > 0 && totalFare < coupon.minOrder) {
        alert(`This coupon requires a minimum order of ₹${coupon.minOrder}.`);
        return;
    }
    
    // Calculate discount
    let discount = 0;
    if (coupon.type === 'percent') {
        discount = Math.round(baseFare * (coupon.discount / 100));
    } else {
        discount = coupon.discount;
    }
    
    // Cap discount to base fare
    discount = Math.min(discount, baseFare);
    
    // Store discount value
    discountInput.value = discount;
    
    // Update savings display
    savingsSpan.textContent = `₹${discount}`;
    msgDiv.style.display = 'flex';
    
    // Update total fare display
    updateTotalWithDiscount(discount);
    
    // Disable input and button
    document.getElementById('coupon-input').disabled = true;
    document.getElementById('apply-coupon-btn').disabled = true;
}

function removeCoupon() {
    const msgDiv = document.getElementById('coupon-applied-msg');
    const discountInput = document.getElementById('coupon-discount-value');
    const couponInput = document.getElementById('coupon-input');
    
    discountInput.value = 0;
    couponInput.value = '';
    couponInput.disabled = false;
    document.getElementById('apply-coupon-btn').disabled = false;
    msgDiv.style.display = 'none';
    
    // Reset total fare
    updateTotalWithDiscount(0);
}

function updateTotalWithDiscount(discount) {
    const pcount = parseInt(document.querySelector("#p-count").value) || 1;
    const baseFare = parseInt(document.querySelector("#basefare").value) * pcount;
    const fee = parseInt(document.querySelector("#fee").value);
    const totalFareEl = document.querySelector(".total-fare-value span");
    
    const newTotal = baseFare + fee - discount;
    
    if (discount > 0) {
        totalFareEl.innerHTML = `<span class="original-price">₹${baseFare + fee}</span> ₹${newTotal}`;
        totalFareEl.parentElement.classList.add('discounted');
    } else {
        totalFareEl.textContent = baseFare + fee;
        totalFareEl.parentElement.classList.remove('discounted');
    }
}