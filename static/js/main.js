$(document).ready(function() {
    closeNav();
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