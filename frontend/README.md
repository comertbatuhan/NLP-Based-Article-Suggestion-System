# Research Paper Finder - Frontend

A modern React application for searching research papers with support for multiple search methods.

## Features

- **Multiple Keywords**: Add and manage multiple search keywords
- **Abstract Search**: Paste one or more paper abstracts for searching
- **Date Range Filter**: Specify publication date range
- **Multiple Search Methods**: Choose between OpenAlex, OpenAI, or NLP-based search
- **Results Modal**: View search results in a modal dialog

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

Build for production:

```bash
npm run build
```

### Preview

Preview the production build:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── SearchPage.jsx      # Main search interface
│   │   ├── SearchPage.css
│   │   ├── ResultsModal.jsx    # Results display modal
│   │   └── ResultsModal.css
│   ├── App.jsx                  # Root component
│   ├── App.css
│   ├── main.jsx                 # Entry point
│   └── index.css               # Global styles
├── index.html                   # HTML template
├── package.json
├── vite.config.js              # Vite configuration
└── README.md
```

## Technologies

- **React 18**: UI library
- **Vite**: Build tool and dev server
- **CSS3**: Styling

