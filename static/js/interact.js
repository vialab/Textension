var canvas, ctx, flag = false,
prevX = 0,
currX = 0,
prevY = 0,
currY = 0,
dot_flag = false,
x = "black",
y = 2,
drawing = false,
haslistener=false;

$(document).ready(function() {
    $(".img-block:not(.img-patch)").on("click", function() {
        if(drawing) return;

        var i = parseInt($(this).attr("id"));
        if(i == 0) {
            return;
        }
        i--;
        toggleSpace($("#"+i.toString()+".img-patch"))
    });

    // $(".img-block").each(function() {
    //     var img = new Image();
    //     img.src = $(this).data("img-src");
    //     var strImage = "url(" + img.src + ")";
    //     $(this).css("background", strImage);
    //     $(this).data("img-src", "");
    // });

    drawConfidence();
    
    $("canvas.text-confidence").hide();
    $("#draw-options").hide();

    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $("canvas.text-confidence").show();            
        } else {
            $("canvas.text-confidence").hide();            
        }
    });

    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
            drawing = true;
            $("canvas#draw-board").removeClass("overlay");
            $("#draw-options").show();
            if(!haslistener) init();
        } else {
            drawing = false;
            $("canvas#draw-board").addClass("overlay");
            $("#draw-options").hide();
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
    if(drawing) return;
    $(".img-patch").removeClass("squeeze");
    $(".img-patch").each(function() {
        $(this).height($(this).data("img-height"));
    });
}

function closeSpaces() {
    if(drawing) return;    
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
            ctx.beginPath();
            ctx.fillStyle = "rgba(244, 167, 66, " + opacity + ")";
            ctx.fillRect(word_blocks[idx][i]["x"], word_blocks[idx][i]["y"], word_blocks[idx][i]["width"], 20);
        }
    });
}

function init() {
    canvas = document.getElementById('draw-board');
    ctx = canvas.getContext("2d");
    canvas.width=$(".vis").width();
    canvas.height=$(".vis").height();
    w = canvas.width;
    h = canvas.height;
    
    if(haslistener) {
        canvas.removeEventListener("mousemove");
        canvas.removeEventListener("mousedown");
        canvas.removeEventListener("mouseup");
        canvas.removeEventListener("mouseout");
    }

    canvas.addEventListener("mousemove", function (e) {
        findxy('move', e)
    }, false);
    canvas.addEventListener("mousedown", function (e) {
        findxy('down', e)
    }, false);
    canvas.addEventListener("mouseup", function (e) {
        findxy('up', e)
    }, false);
    canvas.addEventListener("mouseout", function (e) {
        findxy('out', e)
    }, false);

    haslistener = true;
}

function color(obj) {
    $("#draw-color-select").css("background-color", obj.id);

    switch (obj.id) {
        case "green":
            x = "green";
            break;
        case "blue":
            x = "blue";
            break;
        case "red":
            x = "red";
            break;
        case "yellow":
            x = "yellow";
            break;
        case "orange":
            x = "orange";
            break;
        case "black":
            x = "black";
            break;
        case "white":
            x = "white";
            break;
    }
    if (x == "white") y = 14;
    else y = 2;

}

function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = x;
    ctx.lineWidth = y;
    ctx.stroke();
    ctx.closePath();
}

function erase() {
    var m = confirm("Are you sure you would like to clear?");
    if (m) {
        ctx.clearRect(0, 0, w, h);
        // document.getElementById("canvasimg").style.display = "none";
    }
}

function print() {
    html2canvas($(".vis"), {
        onrendered: function (canvas) {
            theCanvas = canvas;
            document.body.appendChild(canvas);

            // Convert and download as image 
            Canvas2Image.saveAsPNG(canvas);
        }
    });
}

function findxy(res, e) {
    rect = canvas.getBoundingClientRect();
    if (res == 'down') {
        prevX = currX;
        prevY = currY;
        currX = e.clientX - rect.left;
        currY = e.clientY - rect.top;

        flag = true;
        dot_flag = true;
        if (dot_flag) {
            ctx.beginPath();
            ctx.fillStyle = x;
            ctx.fillRect(currX, currY, 2, 2);
            ctx.closePath();
            dot_flag = false;
        }
    }
    if (res == 'up' || res == "out") {
        flag = false;
    }
    if (res == 'move') {
        if (flag) {
            prevX = currX;
            prevY = currY;
            currX = e.clientX - rect.left;
            currY = e.clientY - rect.top;
            draw();
        }
    }
}