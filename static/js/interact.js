$(document).ready(function() {
    $(".img-block").on("click", function() {
        var i = parseInt($(this).attr("id"));
        if(i == 0) {
            return;
        }
        i--;
        $("#"+i.toString()+".img-patch").toggleClass("hidden");
    });

    $(".img-block").each(function() {
        var img = new Image();
        img.src = $(this).data("img-src");
        var strImage = "url(" + img.src + ")";
        $(this).css("background", strImage);
        $(this).data("img-src", "");
    });
}); 


function openSpaces() {
    $(".img-patch").removeClass("hidden");
}

function closeSpaces() {
    $(".img-patch").addClass("hidden");
}