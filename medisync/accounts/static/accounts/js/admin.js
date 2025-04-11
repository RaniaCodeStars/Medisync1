
// Initialize Notyf for notifications
const notyf = new Notyf({
    position: {
        x: 'right',
        y: 'top'
    },
    types: [
        {
            type: 'success',
            background: 'var(--success-color)',
            icon: {
                className: 'fas fa-check-circle',
                tagName: 'i',
                color: '#fff'
            },
            dismissible: true
        },
        {
            type: 'error',
            background: 'var(--danger-color)',
            icon: {
                className: 'fas fa-times-circle',
                tagName: 'i',
                color: '#fff'
            },
            dismissible: true
        }
    ]
});

// Toggle Sidebar
document.getElementById('toggle-sidebar').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('sidebar-collapsed');
});

// Mobile Menu Toggle
document.getElementById('mobile-menu-btn').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('show');
});

// Submenu Toggle
document.querySelectorAll('.has-submenu').forEach(item => {
    item.addEventListener('click', function(e) {
        if (e.target.classList.contains('nav-link')) {
            e.preventDefault();
            const submenu = this.querySelector('.submenu');
            submenu.classList.toggle('show');
            this.classList.toggle('active');
        }
    });
});

// Dark Mode Toggle
document.getElementById('dark-mode-toggle').addEventListener('change', function() {
    document.body.classList.toggle('dark-mode');
    // Save preference to localStorage
    localStorage.setItem('darkMode', this.checked);
    
    // Show notification
    if (this.checked) {
        notyf.success('Mode sombre activé');
    } else {
        notyf.success('Mode clair activé');
    }
});

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    document.getElementById('dark-mode-toggle').checked = true;
    document.body.classList.add('dark-mode');
}

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.top-navbar');
    if (window.scrollY > 10) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Initialize DataTable
$(document).ready(function() {
    $('#recentAppointmentsTable').DataTable({
        responsive: true,
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/fr-FR.json'
        },
        dom: '<"top"f>rt<"bottom"lip><"clear">',
        initComplete: function() {
            // Add search icon
            $('.dataTables_filter input').addClass('form-control');
            $('.dataTables_filter label').contents().filter(function() {
                return this.nodeType === 3;
            }).remove();
            $('.dataTables_filter label').prepend('<i class="fas fa-search me-2"></i>');
        }
    });
});

// Logout Confirmation
document.getElementById('confirmLogout').addEventListener('click', function() {
    // Show logout notification
    notyf.success('Déconnexion réussie. À bientôt!');
    
    // Redirect after delay
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 1500);
});

// Mini Charts for Stats Cards
function createMiniChart(ctx, color, data) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                data: data,
                borderColor: color,
                backgroundColor: 'transparent',
                borderWidth: 3,
                pointRadius: 0,
                tension: 0.4,
                fill: {
                    target: 'origin',
                    above: hexToRgba(color, 0.1)
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    suggestedMin: Math.min(...data) - 5,
                    suggestedMax: Math.max(...data) + 5
                }
            }
        }
    });
}

// Helper function to convert hex to rgba
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Initialize mini charts
const doctorsCtx = document.getElementById('doctorsChart').getContext('2d');
createMiniChart(doctorsCtx, '#7367f0', [12, 19, 15, 25, 22, 30]);

const patientsCtx = document.getElementById('patientsChart').getContext('2d');
createMiniChart(patientsCtx, '#28c76f', [50, 60, 70, 80, 90, 100]);

const appointmentsCtx = document.getElementById('appointmentsChart').getContext('2d');
createMiniChart(appointmentsCtx, '#ff9f43', [30, 40, 35, 45, 50, 55]);

const issuesCtx = document.getElementById('issuesChart').getContext('2d');
createMiniChart(issuesCtx, '#ea5455', [5, 8, 7, 10, 12, 15]);

// Appointments Stats Chart (ApexCharts)
var appointmentsOptions = {
    series: [{
        name: 'Rendez-vous',
        data: [31, 40, 28, 51, 42, 109, 100, 120, 82, 91, 114, 126]
    }, {
        name: 'Confirmés',
        data: [11, 32, 45, 32, 34, 52, 41, 45, 64, 52, 41, 67]
    }],
    chart: {
        height: 350,
        type: 'area',
        toolbar: {
            show: false
        },
        animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: {
                enabled: true,
                delay: 150
            },
            dynamicAnimation: {
                enabled: true,
                speed: 350
            }
        }
    },
    colors: ['#7367f0', '#28c76f'],
    dataLabels: {
        enabled: false
    },
    stroke: {
        curve: 'smooth',
        width: 3,
        dashArray: [0, 5]
    },
    fill: {
        type: 'gradient',
        gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.7,
            opacityTo: 0.3,
            stops: [0, 90, 100]
        }
    },
    xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        labels: {
            style: {
                colors: '#6e6b7b'
            }
        },
        axisBorder: {
            show: false
        }
    },
    yaxis: {
        labels: {
            style: {
                colors: '#6e6b7b'
            }
        }
    },
    tooltip: {
        x: {
            format: 'MMM'
        }
    },
    legend: {
        position: 'top',
        horizontalAlign: 'left',
        labels: {
            colors: '#6e6b7b'
        }
    },
    grid: {
        borderColor: 'rgba(0, 0, 0, 0.05)',
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
            left: 0
        }
    }
};

var appointmentsChart = new ApexCharts(document.querySelector("#appointmentsStatsChart"), appointmentsOptions);
appointmentsChart.render();

// Specialties Chart (ApexCharts)
var specialtiesOptions = {
    series: [44, 55, 13, 43, 22],
    labels: ['Cardiologie', 'Neurologie', 'Pédiatrie', 'Dermatologie', 'Gynécologie'],
    chart: {
        type: 'donut',
        height: 350,
        animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: {
                enabled: true,
                delay: 150
            },
            dynamicAnimation: {
                enabled: true,
                speed: 350
            }
        }
    },
    colors: ['#7367f0', '#28c76f', '#ff9f43', '#ea5455', '#00cfe8'],
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: 200
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    plotOptions: {
        pie: {
            donut: {
                size: '65%',
                labels: {
                    show: true,
                    total: {
                        show: true,
                        label: 'Total',
                        color: '#6e6b7b',
                        formatter: function (w) {
                            return w.globals.seriesTotals.reduce((a, b) => {
                                return a + b
                            }, 0)
                        }
                    },
                    value: {
                        color: '#6e6b7b',
                        formatter: function (val) {
                            return val
                        }
                    }
                }
            }
        }
    },
    legend: {
        position: 'bottom',
        labels: {
            colors: '#6e6b7b'
        }
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 0
    }
};

var specialtiesChart = new ApexCharts(document.querySelector("#specialtiesChart"), specialtiesOptions);
specialtiesChart.render();

// Simulate some button clicks
document.querySelectorAll('.table-btn.edit').forEach(btn => {
    btn.addEventListener('click', function() {
        notyf.success('Action effectuée avec succès');
    });
});

document.querySelectorAll('.table-btn.delete').forEach(btn => {
    btn.addEventListener('click', function() {
        notyf.error('Action annulée');
    });
});
