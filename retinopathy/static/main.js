tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
            colors: {
                // Professional blue/green palette for health-tech
                primary: {
                    light: '#E0F2F1', // teal-50
                    DEFAULT: '#00796B', // teal-700
                    dark: '#004D40', // teal-900
                },
                secondary: {
                    light: '#E3F2FD', // blue-50
                    DEFAULT: '#1E88E5', // blue-600
                    dark: '#0D47A1', // blue-900
                }
            }
        }
    }
}
