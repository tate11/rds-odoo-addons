var print_lables = function(){
	var url = '/labels/print/?customer_name=' + input_customer.value + '&product=' + input_product.value +'&production=' + input_production.value +'&pakage='+qty_package.value+'&codice_articolo_cliente=' + $('#codice_cliente')[0].innerText+'&descrizione='+$('#descrizione_prodotto')[0].innerText;
    var link = document.createElement("a");
    link.download = "to Download";
    link.target = "_blank";

    // Construct the URI
    link.href = url;
    document.body.appendChild(link);
    link.click();

    // Cleanup the DOM
    document.body.removeChild(link);
    delete link;
};

var input_customer = document.getElementById("customer");
var input_product = document.getElementById("product");
var input_production = document.getElementById("production");
var qty_package = document.getElementById("qty_pakage");
var production_producs = [];

$( function() {

	var add_a_item = function(ul, item){
		return $( "<li>" )
		    .data("item.autocomplete", item)
		    .append( "<a>" + item.value + "</a>" )
		    .appendTo( ul );
	};
	
	var update_product = function(item){
        $('#descrizione_prodotto').html(item.name);
        $('#codice_cliente').html(item.customer_code);
        $('#product_image').attr("src", item.image_url);
        input_product.value = item.default_code;
        $('#qty_package').find('option').remove()
        var i;
        var pakages = item.pakage_qty;
        for (i = 0; i < pakages.length; i++) { 
        	qty_package.append('<option value="' + pakages[i][1].toString() + '">' + pakages[i][0].toString() + '</option>');
        }
	};



	$('#production').autocomplete({
        source: function( request, response ) {
        	$.ajax({url: '/labels/production/?name=' + input_production.value.toUpperCase(),
      		  	    type: 'get',
      		  	    data: {term: request.term},
      		  	    success: function( data ) {data = $.parseJSON(data);
      		  	   							  response( data );}
      	  		});
        },
        create: function() {
            $(this).data('ui-autocomplete')._renderItem = function (ul, item) 
            	{
            	return add_a_item(ul, item);};
        },
        minLength: 2,
        select: function( event, ui ) {
        	if (ui.item.products.length>0){
        		update_product(ui.item.products[0])
        		production_producs = ui.item.products;
        	}
        	else{
        		production_producs=[]
        	}
        	if(ui.item.customer){
        		$('#codice_cliente').html(ui.item.customer_code);
        		add_a_item($('#customer'), ui.item);
        	}
          }
	} ); //autocomlete enbd
    
	$('#customer').autocomplete({
      source: function( request, response ) {
    	  $.ajax({url: '/labels/customers/?name=' + input_customer.value.toUpperCase(),
    		  	   type: 'get',
    		  	   data: {term: request.term},
    		  	   success: function( data ) {data = $.parseJSON(data);
    		  	   							  response( data );}
    	  		});
      },
      create: function() {
          $(this).data('ui-autocomplete')._renderItem = function (ul, item) 
          	{
        	  return $( "<li>" )
        	    .data("item.autocomplete", item)
        	    .append( "<a>" + item.value + "</a>" )
        	    .appendTo( ul );
          	};
      },
      minLength: 2,
    } );

	$('#product').autocomplete({
        source: function( request, response ) {
	      	if (production_producs.length>0){
	      		response( production_producs );
	      	}
	      	else{
	        	$.ajax({url: '/labels/products/?name=' + input_product.value.toUpperCase(),
	      		  	   type: 'get',
	      		  	   data: {term: request.term},
	      		  	   success: function( data ) {data = $.parseJSON(data);
	      		  	   							  response( data );}
	      	  		});
	      	}
      	},
        create: function() {
            $(this).data('ui-autocomplete')._renderItem = function (ul, item) 
            	{return $( "<li>" )
          	    	.data("item.autocomplete", item)
          	    	.append( "<a>" + item.display_name + "</a>" )
          	    	.appendTo( ul );};
        },
        minLength: 2,
        select: function( event, ui ) {
        	update_product(ui.item);
        }
      }); //autocomplete end

} );



