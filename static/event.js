

$('#select-form').on('change', (evt) => {

  let formInput = {act_id: $(evt.target).val()};

  $.get('/api/activity', formInput, (res) => {

    console.log("activity res:", res); 
      // returns the res object for a selected activity, e.g.: 
      // {act_id: 6, act_name: "walking", act_unit: "steps"}
    $('#act_unit').html(res.act_unit);

    $('#summary_header').html(`Summary of ${res.act_name} (in ${res.act_unit}):`);
  });


  $.get('/api/events', formInput, (res) => {

    console.log("event results:", res);
    
    $('#events').empty();

    for (let event of res) {
      $('#events').append(`<li>${event.event_date}: ${event.event_amt} 
        ${event.unit}</li>`);
    }
  });
});
