//window.onload = dateInputText();

function dateInputText() {
  //document.querySelector("#reset-button").on("click", function(){
  document.querySelector(".DateInput > #endDate").addEventListener('change', function(e){
    console.log("End date change detected!");
    if (this.value == "Invalid date") {
      this.value = "END DATE";
    }
  });

}
