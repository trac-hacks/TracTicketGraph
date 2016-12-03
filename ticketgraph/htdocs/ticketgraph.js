jQuery(document).ready(function($) {
	$('#ticketgraph').find('input').hide().end()
		.find('select').change(function() {
			$('#ticketgraph').submit();
		});

	var $placeholder = $('#placeholder');
	$placeholder.width(800).height(500);
	var barSettings = { show: true, barWidth: 86400000 };
	$.plot($placeholder,
	[
		{
			data: closedTickets,
			label: 'Closed',
			bars: barSettings,
			color: '#8b0000'
		},
		{
			data: openedTickets,
			label: 'New',
			bars: barSettings,
			color: '#66cd00',
			stack: true
		},
		{
			data: reopenedTickets,
			label: 'Reopened',
			bars: barSettings,
			color: '#458b00',
			stack: true
		},
		{
			data: openTickets,
			label: 'Open',
			yaxis: 2,
			lines: { show: true, steps: false },
			shadowSize: 0,
			color: '#333'
		}
	],
	{
		xaxis: { mode: 'time', minTickSize: [1, "day"] },
		yaxis: { label: 'Tickets' },
		y2axis: { min: 0 },
		legend: { position: 'sw' }
	});
});
