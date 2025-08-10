# Tournament Manager

A web application for creating and managing sports tournaments. Easily organize teams into groups, shuffle team assignments, and manage tournament progression.

## Features

- Create tournaments with custom team configurations
- Organize teams into multiple groups
- Shuffle teams randomly between groups
- Track tournament dates and status
- Responsive design with Tailwind CSS

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd league-builder
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8080/
   ```

## Project Structure

```
league-builder/
├── app.py                # Main application file
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── create_league.html # League creation form
    └── view_league.html  # League schedule view
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
