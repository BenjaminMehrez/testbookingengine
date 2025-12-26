Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

function onDateUpdate(){
    const inputCheckin = document.querySelector("#id_checkin").value;
    const inputCheckout = document.querySelector("#id_checkout").value;

    // if no checkin or checkout, total days is 0
    if (!inputCheckin || !inputCheckout) {
        document.querySelector("#total-days").innerHTML = "0"; // O un guion "-"
        return; // Salimos de la función
    }

    const date1 = new Date(inputCheckin);
    const date2 = new Date(inputCheckout);

    const diffTime = date2.getTime() - date1.getTime();

    if (!isNaN(diffTime)) {
        const diffDays = diffTime / (1000*3600*24);
        // Opcional: Evitar números negativos visuales si checkin > checkout
        document.querySelector("#total-days").innerHTML = diffDays > 0 ? diffDays : 0;
    } else {
        document.querySelector("#total-days").innerHTML = "0";
    }

}

document.querySelector("#id_checkout").addEventListener("change",(e)=>{
    onDateUpdate()
    document.querySelector("#id_guests").focus()
    
})
document.querySelector("#id_checkin").addEventListener("change",(e)=>{
    const checkout=document.querySelector("#id_checkout")

    const tomorrow=new Date(e.target.value).addDays(1).toISOString().split('T')[0]
    if(e.target.value>checkout.value){
        checkout.setAttribute("value",tomorrow)
        
    }
    onDateUpdate()
    checkout.setAttribute("min",tomorrow)
    // FIX: Only focus if the field exists
    const guestInput = document.querySelector("#id_guests");
    if (guestInput) {
        guestInput.focus();
    }
})
