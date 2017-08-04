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

    drawConfidence();
    $("canvas.text-confidence").hide();

    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $("canvas.text-confidence").show();            
        } else {
            $("canvas.text-confidence").hide();            
        }
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

function drawConfidence() {
    $(".img-block:not(.img-patch)").each(function(idx) {
        var canvas = $("canvas.text-confidence", this)[0];
        var ctx = canvas.getContext("2d");
        ctx.canvas.width = $(this).width();
        ctx.canvas.height = $(this).height();
        for(var i=0; i<word_blocks[idx].length; i++) {
            var opacity = (word_blocks[idx][i]["confidence"]/100.0)*0.8;
            console.log(word_blocks[idx][i]["x"]);
            ctx.beginPath();
            ctx.fillStyle = "rgba(244, 167, 66, " + opacity + ")";
            ctx.fillRect(word_blocks[idx][i]["x"], word_blocks[idx][i]["y"], word_blocks[idx][i]["width"], 20);
        }
    });
}