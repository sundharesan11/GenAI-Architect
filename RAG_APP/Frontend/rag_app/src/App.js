import logo from './logo.svg';
import './App.css';
import QuestionForm from './questionForm';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          <QuestionForm />
        </p>
       
      </header>
    </div>
  );
}

export default App;
