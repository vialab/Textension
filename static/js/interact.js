$(document).ready(function() {
    $(".img-block:not(.img-patch)").on("click", function() {
        var i = parseInt($(this).attr("id"));
        if(i == 0) {
            return;
        }
        i--;
        toggleSpace($("#"+i.toString()+".img-patch"))
    });

    $(".img-block").each(function() {
        var img = new Image();
        img.src = $(this).data("img-src");
        var strImage = "url(" + img.src + ")";
        $(this).css("background", strImage);
        $(this).data("img-src", "");
    });
}); 

function toggleSpace($elem) {
    if($elem.hasClass("squeeze")) {
        $elem.removeClass("squeeze");
        $elem.height($elem.data("img-height"));
    } else {
        $elem.height(0);
        $elem.addClass("squeeze");        
    }
}

function openSpaces() {
    $(".img-patch").removeClass("squeeze");
    $(".img-patch").each(function() {
        $(this).height($(this).data("img-height"));
    });
}

function closeSpaces() {
    $(".img-patch").height(0);
    $(".img-patch").addClass("squeeze");    
}