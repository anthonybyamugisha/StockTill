import { Route, Routes } from 'react-router-dom';
import { appRouter } from './app/router';

function App() {
  return <Routes>{appRouter}</Routes>;
}

export default App;
