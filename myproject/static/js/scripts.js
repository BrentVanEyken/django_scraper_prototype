// Wait for the DOM to fully load
document.addEventListener('DOMContentLoaded', function() {
    // Handle "Scrape All Datapoints" Form Submission
    const scrapeAllForm = document.getElementById('scrape-all-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const scrapeAllButton = document.getElementById('scrape-all-button');

    if (scrapeAllForm && loadingOverlay && scrapeAllButton) {
        scrapeAllForm.addEventListener('submit', function(event) {
            // Show the loading overlay
            loadingOverlay.style.display = 'flex';
            
            // Disable the button to prevent multiple submissions
            scrapeAllButton.disabled = true;
            scrapeAllButton.innerText = 'Scraping...';
        });
    }

    // Handle "Test XPath" Form Submission
    const testXpathForm = document.getElementById('test-xpath-form');
    const testXpathButton = document.getElementById('test-xpath-button');

    if (testXpathForm && loadingOverlay && testXpathButton) {
        testXpathForm.addEventListener('submit', function(event) {
            // Show the loading overlay
            loadingOverlay.style.display = 'flex';
            
            // Disable the button to prevent multiple submissions
            testXpathButton.disabled = true;
            testXpathButton.innerText = 'Scraping...';
        });
    }

    // Resizable Panels Functionality
    const resizer = document.getElementById('resizer');
    const filtersPanel = document.getElementById('filters-panel');
    const tablePanel = document.getElementById('table-panel');

    if (resizer && filtersPanel && tablePanel) {
        let x = 0;
        let filtersWidth = 0;

        const mouseDownHandler = function(e) {
            x = e.clientX;
            filtersWidth = filtersPanel.getBoundingClientRect().width;

            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        };

        const mouseMoveHandler = function(e) {
            const dx = e.clientX - x;
            const newFiltersWidth = filtersWidth + dx;

            // Set minimum and maximum widths
            if (newFiltersWidth < 200) {
                filtersPanel.style.width = '200px';
            } else if (newFiltersWidth > 600) {
                filtersPanel.style.width = '600px';
            } else {
                filtersPanel.style.width = `${newFiltersWidth}px`;
            }
        };

        const mouseUpHandler = function() {
            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
        };

        resizer.addEventListener('mousedown', mouseDownHandler);
    }

    // Initialize DataTables
    const dataTable = $('#datapoints-table').DataTable({
        "paging": true,
        "searching": true,
        "ordering": true,
        "order": [[8, "desc"]], // Default ordering by 'Last Updated' column
        "columnDefs": [
            { "orderable": false, "targets": [3, 4, 5, 6] } // Disable ordering on specific columns if needed
        ],
        "lengthMenu": [10, 25, 50, 100],
        "pageLength": 10,
        "autoWidth": false, // Disable automatic column width calculation
        "responsive": true, // Make the table responsive
        "language": {
            "emptyTable": "No datapoints found."
        }
    });

    // Initialize colResizable after DataTables
    $('#datapoints-table').colResizable({
        liveDrag: true,
        gripInnerHtml: "<div class='grip'></div>",
        draggingClass: "dragging",
        resizeMode: 'fit'
    });

    // Handle Toggle Filters Button
    const toggleFiltersButton = document.getElementById('toggle-filters');
    const toggleIcon = document.getElementById('toggle-icon');

    if (toggleFiltersButton && filtersPanel && resizer && tablePanel) {
        toggleFiltersButton.addEventListener('click', function() {
            const isVisible = filtersPanel.style.display !== 'none';
            if (isVisible) {
                // Hide Filters Panel
                filtersPanel.style.display = 'none';
                resizer.style.display = 'none';
                toggleIcon.classList.remove('bi-filter-left');
                toggleIcon.classList.add('bi-filter-right');
            } else {
                // Show Filters Panel
                filtersPanel.style.display = 'block';
                resizer.style.display = 'block';
                toggleIcon.classList.remove('bi-filter-right');
                toggleIcon.classList.add('bi-filter-left');
            }
        });
    }
});
