const pay = document.getElementById("pilot-pay");
const status = document.getElementById("pilot-status");

pay.addEventListener("click", () => {
  if (typeof window.Razorpay !== "function") {
    status.textContent = "Checkout could not load. Refresh and try again.";
    return;
  }
  const checkout = new window.Razorpay({
    key: pay.dataset.key,
    order_id: pay.dataset.order,
    amount: Number(pay.dataset.amount),
    currency: "INR",
    name: "ApplyPost",
    description: "Pilot access (test)",
    handler: () => {
      status.textContent = "Test checkout returned. Access stays pending until server confirmation.";
    },
  });
  checkout.open();
});
