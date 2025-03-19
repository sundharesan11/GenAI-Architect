import './App.css';
import UploadForm from './uploadData';
import QuestionForm from './questionForm';

function App() {
  return (
    <div className="App">
      
      <header className="App-header">
      <div className="header-logo">RAG Application</div>
      </header>
      <div>
          <UploadForm />
      </div>
      <div>
          <QuestionForm />
      </div>
    </div>
  );
}

export default App;
