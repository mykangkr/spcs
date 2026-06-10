import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div>
      <h1>Welcome</h1>
      <p>
        This is the home page. Go to your <Link to="/tasks">tasks</Link>.
      </p>
    </div>
  )
}

export default HomePage
