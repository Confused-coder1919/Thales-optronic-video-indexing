export default function AttributionPage() {
  return (
    <div className="stack">
      <h1 className="h1">Attribution</h1>
      <div className="card">
        <div className="card-body stack">
          <p className="lead">
            This web app is based on the document:
            <br />
            <strong>CyberEdu v1.1 — February 2017</strong> (quiz modules 1–4, questions 1–94),
            provided by <strong>ANSSI</strong>.
          </p>
          <div className="hr" />
          <p className="lead">
            Original license/credit (from the PDF):
            <br />
            <strong>Creative Commons Attribution 3.0 France</strong>.
            <br />
            The document was written by a consortium of teacher-researchers and cybersecurity
            professionals and made available by ANSSI.
          </p>
          <div className="hr" />
          <p className="lead">
            This app includes:
            <br />
            English translation of the prompts and choices, plus additional explanations and theory
            cards to support learning.
          </p>
          <p className="lead">
            No backend is used. All results are stored locally in your browser and can be exported
            as JSON.
          </p>
        </div>
      </div>
    </div>
  );
}

