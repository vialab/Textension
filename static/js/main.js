// import * as modal from './modules/modal.js';


function downloadText() {
    let file = new Blob([JSON.stringify(ocr, null, 2)], { type: "application/json" })
    let link = document.getElementById('download_data')
    let url = URL.createObjectURL(file);

    // Convert and download as image 
    link.setAttribute('href', url);
    link.setAttribute('download', 'Textension.txt');
    link.click();
}


$(document).ready(function() {
    closeNav();

    if (typeof togglePageOptions === "function") {
        togglePageOptions();
    }


    // document.on("addedfiles", function(files) {
    //     console.log("added files event  ",files)
    // })

    $('[data-toggle="tooltip"]').tooltip({ container: 'body' })
});




/// open the side bar containing the tools
function openNav() {
    var width = ($(".tool-box").width()+5).toString() + "px";    
    $(".tool-box").css({"transform":"translateX(0px)"});
    $(".tool-box").addClass("opened");
    // $(".stage").css({"transform":"translateX(" + width + ")"});
}

// close the side bar containing the tools
function closeNav() {
    var width = "-" + ($(".tool-box").width()+5).toString() + "px";
    $(".tool-box").css({"transform":"translateX(" + width + ")"});
    $(".tool-box").removeClass("opened");
    // $(".stage").css({"transform":"translateX(0px)"});
}