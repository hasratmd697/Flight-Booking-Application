function popup(element) {
    let ref = element.dataset.ref;
    document.querySelector("#cancel_ticket_btn").dataset.ref = ref;
    document.querySelector(".popup").style.display = 'block';
}

function remove_popup() {
    document.querySelector(".popup").style.display = 'none';
    document.querySelector("#cancel_ticket_btn").dataset.ref = "";
}

function cancel_tkt() {
    let ref = document.querySelector("#cancel_ticket_btn").dataset.ref;
    let formData = new FormData();
    formData.append('ref',ref)
    fetch('ticket/cancel',{
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(response => {
        if (response.success === true) {
            remove_popup();
            document.querySelector(`[id='${ref}'] .ticket-action-div`).innerHTML = '';
            document.querySelector(`[id='${ref}'] .status-div`).innerHTML = `<div class="red">CANCELLED</div>`;
            document.querySelector(`[id='${ref}'] .booking-date-div`).innerHTML = '';
        }
        else {
            remove_popup();
            alert(`Error: ${response.error}`)
        }
    });
}

function resendEmail(element) {
    let ref = element.dataset.ref;
    let btn = element;
    
    // Disable button and show loading state
    btn.disabled = true;
    btn.innerHTML = '⏳';
    
    let formData = new FormData();
    formData.append('ref_no', ref);
    
    fetch('/flight/ticket/resend-email', {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(response => {
        if (response.success === true) {
            btn.innerHTML = '✅';
            btn.classList.remove('btn-outline-success');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = '📧';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
                btn.disabled = false;
            }, 3000);
            alert(response.message);
        } else {
            btn.innerHTML = '📧';
            btn.disabled = false;
            alert(`Error: ${response.message}`);
        }
    })
    .catch(error => {
        btn.innerHTML = '📧';
        btn.disabled = false;
        alert('Failed to send email. Please try again.');
    });
}