/******************************************************************************
 * event.js
 * Instantiate all our interactions for digital object on /interact page
 * This is mostly the widget button functionality in our side bar
 *****************************************************************************/

$(document).ready(function() {
    $(".img-box").each(function(i, $box) {
        let w = 0;
        $(".img-cell", $box).each(function(j, cell) {
            $(cell).css("left", w+"px");
            w += $(cell).width();
        });
    });
    closeNav(); // start with tool bar closed
    resizeStage(); // handle the resizing of the window and recalculate margins

    // click event listener for lines to be toggled opened or closed
    $(".img-block:not(.img-patch)").on("click", function() {
        if (getActiveMode() != "vertical") return; // proper mode needed
        let id = parseInt($(this).attr("id"));
        if(id == 0) return; // the first line of the page doesn't need space
        toggleSingleSpace($("#"+id.toString()+".img-patch"), false)
    });

    injectMetaData(); // insert the OCR text into the html elements
    drawOverlays(); // draw our graphs that the user can interact with
    $(".text-confidence").hide();

    // instantiate our OCR confidence highlight button
    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $(".text-confidence").show();            
        } else {
            $(".text-confidence").hide();            
        }
    });

    // drawUniqueness();
    // instantiate our uniqueness tool
    $("#uniqueness-range").hide();
    $("#uniqueness").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);
            setUniqueness( $("#uniqueness-range input").val() );
            $("#uniqueness-range").show();
            $(".switch").css("height", "15%");
        } else {
            $(".patch-box span.uniqueness-bar").height(0);
            $("#uniqueness-range").hide();
            $(".switch").css("height", "16%");
        }
    });

    // we use range sliders for things like year
    let rangeSlider = function(){
        let slider = $('.range-slider'),
            range = $('.range-slider__range'),
            value = $('.range-slider__value');
        slider.each(function(){
        
            value.each(function(){
            let value = $(this).prev().attr('value');
            $(this).html(value);
            });
        
            range.on('input', function(){
            $(this).next(value).html(this.value);
            });
        });
    };
    rangeSlider();

    // Ngram usage widget buttom
    // drawNGramUsage();
    $(".ngram-usage").hide();
    $("#ngram").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);            
            $(".ngram-usage").show();
        } else {
            $(".ngram-usage").hide();            
        }
    });

    // Maps widget button
    drawLocations();    
    $(".entity-location").hide();
    $("#entity-map-container").hide();
    $("#location").on("click", function() {
        if($(this).is(":checked")) {
            $(".entity-location").show();
            $("#entity-map-container").show();
        } else {
            $(".entity-location").hide();
            $("#entity-map-container").hide();
        }
        resizeStage();
    });

    // Translation widget button
    $("#translate-text").on("click", function() {
        if($(this).is(":checked")) {
            if( $("#ocr-text").is(":checked") ) {
                $("#ocr-text").click();
            }
            $(".img-patch-text").each(function(idx) {
                $(this).val(translation[idx]);
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    // OCR widget button
    $("#ocr-text").on("click", function() {
        if($(this).is(":checked")) {
            if($("#translate-text").is(":checked")) {
                $("#translate-text").click();
            }
            $(".img-patch-text").each(function(idx) {
                $(this).val(ocr[idx]);
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    // Pronoun replacement widget button {
    $("#replace-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            $(".gender-pronoun").show();
        } else {
            fixPronouns();
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            $(".gender-pronoun").hide();
        }
    });

    $("#male-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            replacePronouns(false);
        } else {
            fixPronouns();
        }
    });

    $("#female-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            replacePronouns(true);
        } else {
            fixPronouns();
        }
    });
    // } end of pronoun replacement buttons

    // ACTIVE TOOLS - tools that alter the left click functionality
    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
            setActiveMode("draw");
            $("canvas#draw-board").removeClass("overlay");
            $("#draw-options").show();
            if(!haslistener) init();
        } else {
            setActiveMode("");
            $("#draw-options").hide();            
        }
    });

    $(".img-block:not(.img-patch) img").on("click", function() {
        switch(getActiveMode()) {
            case "eraser":
                eraseWord($(this));
                break;
            case "horizontal":
                if($(this).hasClass("img-text")) {
                    let str_id = $(this).attr("id");
                    str_id = str_id.replace("text", "space");
                    toggleSingleSpace($("#"+str_id), true)
                }
                break;
            case "grammar":
            case "draw":
            case "vertical":
            default:
                return;
        }
    });

    $(".img-block:not(.img-patch) img").on("mousedown", function() {
        mouse_down = true;
        let action;
        switch(getActiveMode()) {
            case "define":
                action = defineWord;
                break;
            case "context":
                action = createContextMap;
                break;
            default:
                return;
        }
        timeout_id = setTimeout(action($(this)), 1000);
    }).on("mouseup mouseleave", function() {
        mouse_down = false;
        switch(getActiveMode()) {
            case "define":
                $(this).popover("hide");
                break;
            case "context":
                break;
            default:
                return;
        }
        clearTimeout(timeout_id);
    });
    // END ACTIVE TOOLS

    $("#vis-container").css("opacity", 1);
    $("#loading").removeClass("show");
});