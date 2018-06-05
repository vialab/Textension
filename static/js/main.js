$(document).ready(function() {
//     $("#main-nav").peekaboo({
//         offset_top: 60
//         , scroll_threshold: 20
//         , opaque_threshold_down: 25
//         , opaque_threshold_up: 25
//         , animation: true
//         , hide_class: "slide-up"
//         , fade_class: "fade-background"
//         , hide_height_auto: true
//     });
    closeNav();
});

function openNav() {
    var width = ($(".tool-box").width()+5).toString() + "px";    
    $(".tool-box").css({"transform":"translateX(0px)"});
    $(".tool-box").addClass("opened");
    // $(".stage").css({"transform":"translateX(" + width + ")"});
}

function closeNav() {
    var width = "-" + ($(".tool-box").width()+5).toString() + "px";
    $(".tool-box").css({"transform":"translateX(" + width + ")"});
    $(".tool-box").removeClass("opened");
    // $(".stage").css({"transform":"translateX(0px)"});
}